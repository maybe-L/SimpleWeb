from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from .forms import RegistrationForm, LoginForm, WebsiteSetupForm
from .models import User, UserWebsiteData, Menu
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from . import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/demo')
def demo():
    return render_template('classicdemo.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)  # 비밀번호 해시화
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Login successful: {user.username}!', 'success')
            return redirect(url_for('main.setup'))  # 설정 페이지로 리디렉션
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', form=form)

@bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    form = WebsiteSetupForm()
    if form.validate_on_submit():
        # URL 중복 확인
        existing_website = UserWebsiteData.query.filter_by(website_url=form.website_url.data).first()
        if existing_website:
            flash('This website URL is already taken. Please choose another one.', 'danger')
            return render_template('setup.html', form=form)

        # 웹사이트 데이터 저장
        website_url = form.website_url.data
        website_name = form.website_name.data

        user_website_data = UserWebsiteData(
            user_id=current_user.id,
            website_url=website_url,
            website_name=website_name,
        )
        db.session.add(user_website_data)
        db.session.commit()

        # 메뉴 데이터 저장
        index = 1
        while True:
            menu_name_field = f'menu_name_{index}'
            menu_type_field = f'menu_type_{index}'
            menu_name = request.form.get(menu_name_field)
            menu_type = request.form.get(menu_type_field)
            if menu_name and menu_type:
                menu = Menu(
                    name=menu_name,
                    type=menu_type,
                    website_id=user_website_data.id
                )
                db.session.add(menu)
                index += 1
            else:
                break
        db.session.commit()

        # 성공적으로 저장된 경우 main 페이지로 리디렉션
        flash('Website setup completed!', 'success')
        return redirect(url_for('main.user_website', website_url=website_url))  # 메인 페이지로 리디렉션

    else:
        flash("Form submission failed. Please check the required fields.", 'danger')

    return render_template('setup.html', form=form)



@bp.route('/check_url', methods=['GET'])
def check_url():
    website_url = request.args.get('website_url')
    if not website_url:
        return jsonify({'available': False, 'message': 'No URL provided'}), 400

    # 데이터베이스에서 해당 URL을 검색
    existing_website = UserWebsiteData.query.filter_by(website_url=website_url).first()

    if existing_website:
        return jsonify({'available': False, 'message': 'This URL is already taken'}), 200
    else:
        return jsonify({'available': True, 'message': 'This URL is available'}), 200




@bp.route('/<string:website_url>/editor', methods=['GET', 'POST'])
@login_required
def home_editor(website_url):
    # Get the website data
    user_website_data = UserWebsiteData.query.filter_by(website_url=website_url).first_or_404()

    if request.method == 'POST':
        # Save edited content for the homepage
        content = request.form.get('content')
        if content:
            user_website_data.home_content = content  # 홈페이지 컨텐츠로 저장
            db.session.commit()
            flash('Home content saved!', 'success')
        else:
            flash('No content provided.', 'danger')

        # After saving, stay in edit mode
        return redirect(url_for('main.home_editor', website_url=website_url))

    # Render the home editor
    return render_template('home_editor.html', website_data=user_website_data, body_class='edit-mode')




@bp.route('/<string:website_url>/<string:menu_name>/editor', methods=['GET', 'POST'])
@login_required
def menu_editor(website_url, menu_name):
    # Get the website and menu data
    user_website_data = UserWebsiteData.query.filter_by(website_url=website_url).first_or_404()
    menu = Menu.query.filter_by(website_id=user_website_data.id, name=menu_name).first_or_404()

    if request.method == 'POST':
        # Save edited content
        content = request.form.get('content')

        if content and menu:
            # 컨텐츠와 메뉴가 유효할 때만 저장
            menu.content = content
            db.session.commit()
            flash('Changes saved!', 'success')
        else:
            flash('No content or invalid menu.', 'danger')

        # After saving, stay in edit mode
        return redirect(url_for('main.menu_editor', website_url=website_url, menu_name=menu_name))

    # Render the editor for the specific menu
    if menu.type == 'list':
        return render_template('list_editor.html', website_data=user_website_data, menu=menu, body_class='edit-mode')
    elif menu.type == 'gallery':
        return render_template('gallery_editor.html', website_data=user_website_data, menu=menu, body_class='edit-mode')
    elif menu.type == 'home':  
        return render_template('home_editor.html', website_data=user_website_data, menu=menu, body_class='edit-mode')
    else:
        return "Menu type not found", 404







@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/save', methods=['POST'])
@login_required
def save_content():
    data = request.get_json()
    menu_id = data.get('menu_id')
    content = data.get('content')
    
    menu = Menu.query.filter_by(id=menu_id).first()
    if menu and menu.website.user_id == current_user.id:
        menu.content = content
        db.session.commit()
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'No content found'})

@bp.route('/<string:website_url>')
def user_website(website_url):
    user_website_data = UserWebsiteData.query.filter_by(website_url=website_url).first_or_404()
    
    # URL에 '/edit'가 포함된 경우 body_class를 'edit-mode'로 설정
    if '/edit' in request.path:
        return render_template('main_page.html', website_data=user_website_data, body_class='edit-mode')
    else:
        return render_template('main_page.html', website_data=user_website_data, body_class='')



@bp.route('/<string:website_url>/<string:menu_name>')
def menu_page(website_url, menu_name):
    # 해당 유저의 웹사이트 데이터를 가져옴
    user_website_data = UserWebsiteData.query.filter_by(website_url=website_url).first_or_404()
    
    # 선택한 메뉴를 가져옴
    menu = Menu.query.filter_by(website_id=user_website_data.id, name=menu_name).first_or_404()

    # 메뉴 타입에 따라 템플릿 결정
    menu_type = menu.type

    # 어드민 바를 유지하려면 website_data와 로그인 정보 포함
    if menu_type == 'list':
        return render_template('list_page.html', menu_name=menu_name, menu=menu, website_data=user_website_data, body_class='')
    elif menu_type == 'gallery':
        return render_template('gallery_page.html', menu_name=menu_name, menu=menu, website_data=user_website_data, body_class='')
    elif menu_type == 'home':
        return render_template('home_page.html', menu_name=menu_name, menu=menu, website_data=user_website_data, body_class='')
    else:
        return "Menu type not found", 404


