from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from .forms import RegistrationForm, LoginForm, WebsiteSetupForm, MenuEditForm
from .models import User, UserWebsiteData, Menu, Image
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from werkzeug.utils import secure_filename
from flask import current_app
from flask_wtf import FlaskForm
from wtforms import TextAreaField, HiddenField  # 여기에 필요한 필드들을 임포트
from sqlalchemy.exc import IntegrityError


import os


bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # 중복 이메일 확인
        existing_email = User.query.filter_by(email=email).first()
        
        if existing_email:
            flash('Email is already registered. Please use a different email.')
            return redirect(url_for('main.register'))

        # 사용자 등록 (중복된 사용자 이름 허용)
        new_user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        
        try:
            db.session.commit()
            flash('Account created successfully!')
            return redirect(url_for('main.login'))
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while creating the account. Please try again.')
            return redirect(url_for('main.register'))

    # GET 요청일 때, 회원가입 폼을 렌더링
    return render_template('register.html', form=form)


@bp.route('/check_email', methods=['GET'])
def check_email():
    email = request.args.get('email')

    # 입력된 이메일이 없는 경우 처리
    if not email:
        return jsonify({'exists': False, 'message': 'No email provided'}), 400

    # 데이터베이스에서 해당 이메일을 검색
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        # 중복된 이메일이 있을 경우
        return jsonify({'exists': True, 'message': 'Email is already taken'}), 200
    else:
        # 중복되지 않은 경우
        return jsonify({'exists': False, 'message': 'Email is available'}), 200




@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Login successful: {user.username}!', 'success')

            # 유저의 웹사이트 및 메뉴 데이터 확인
            user_website_data = UserWebsiteData.query.filter_by(user_id=user.id).first()

            if user_website_data:
                # 웹사이트 URL로 리디렉션
                return redirect(url_for('main.user_website', website_url=user_website_data.website_url))

            return redirect(url_for('main.setup'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))



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


@bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    form = WebsiteSetupForm()

    # 현재 유저의 웹사이트 데이터를 가져옴
    user_website_data = UserWebsiteData.query.filter_by(user_id=current_user.id).first()

    if form.validate_on_submit():
        website_url = form.website_url.data if not user_website_data else user_website_data.website_url
        website_name = form.website_name.data if form.website_name.data else user_website_data.website_name

        if not user_website_data:
            # 새로 생성
            user_website_data = UserWebsiteData(
                user_id=current_user.id,
                website_url=website_url,
                website_name=website_name,
            )
            db.session.add(user_website_data)
        else:
            # 웹사이트 이름이 변경된 경우 업데이트
            if user_website_data.website_name != website_name:
                user_website_data.website_name = website_name

        db.session.commit()

        # 메뉴 데이터 처리
        index = 1  # 메뉴 순서 지정
        while True:
            menu_name_field = f'menu_name_{index}'
            menu_type_field = f'menu_type_{index}'
            menu_order_field = f'menu_order_{index}'
            menu_name = request.form.get(menu_name_field)
            menu_type = request.form.get(menu_type_field)
            menu_order = request.form.get(menu_order_field)

            if menu_name and menu_type:
                # 기존 메뉴가 있는 경우 업데이트, 없으면 새로 추가
                menu = Menu.query.filter_by(website_id=user_website_data.id, name=menu_name).first()
                if menu:
                    menu.type = menu_type
                    menu.order = int(menu_order) if menu_order else index  # 메뉴 순서 업데이트
                else:
                    new_menu = Menu(
                        name=menu_name,
                        type=menu_type,
                        order=int(menu_order) if menu_order else index,  # 새로운 메뉴의 순서 지정
                        website_id=user_website_data.id
                    )
                    db.session.add(new_menu)
                index += 1
            else:
                break

        db.session.commit()

        # order=1인 메뉴가 메인 페이지가 되어야 함
        main_menu = Menu.query.filter_by(website_id=user_website_data.id, order=1).first()

        if not main_menu:
            flash('Main menu could not be set. Please try again.', 'danger')
            return redirect(url_for('main.setup'))


        # 성공적으로 저장된 경우 메인 페이지로 리디렉션
        flash('Website updated successfully!', 'success')
        return redirect(url_for('main.user_website', website_url=user_website_data.website_url))

    return render_template('setup.html', form=form, website_data=user_website_data, enumerate=enumerate)


@bp.route('/<string:website_url>', methods=['GET'])
def user_website(website_url):
    # 웹사이트 데이터 가져오기
    user_website_data = UserWebsiteData.query.filter_by(website_url=website_url).first_or_404()

    # 메인 메뉴(order=1) 가져오기
    main_menu = Menu.query.filter_by(website_id=user_website_data.id, order=1).first_or_404()

    # 나머지 메뉴들 가져오기
    menus = Menu.query.filter_by(website_id=user_website_data.id).order_by(Menu.order).all()

    # 템플릿 렌더링 시 main_menu와 menus를 전달
    return render_template(f'{main_menu.type}_page.html', menu=main_menu, website_data=user_website_data, menus=menus)



@bp.route('/<string:website_url>/<string:menu_name>', methods=['GET'])
def menu_page(website_url, menu_name):
    # /<menu_name> 형식으로 다른 메뉴들 처리
    user_website_data = UserWebsiteData.query.filter_by(website_url=website_url).first_or_404()
    menu = Menu.query.filter_by(website_id=user_website_data.id, name=menu_name).first_or_404()

    return render_template(f'{menu.type}_page.html', menu=menu, website_data=user_website_data)


@bp.route('/<string:website_url>/editor', methods=['GET', 'POST'])
@login_required
def main_menu_editor(website_url):
    # Get the website data
    user_website_data = UserWebsiteData.query.filter_by(website_url=website_url).first_or_404()

    # 첫 번째 메뉴(order=1)를 메인 페이지로 사용
    main_menu = Menu.query.filter_by(website_id=user_website_data.id, order=1).first()

    # 폼을 초기화
    form = MenuEditForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            content = form.content.data
            if content:
                main_menu.content = content  # 메뉴의 내용을 저장
                # 메뉴의 순서는 건드리지 않음
                db.session.commit()
                flash('Main page content saved!', 'success')
            else:
                flash('No content provided.', 'danger')

        # 저장 후에도 에디터 모드에 남아있음
        return redirect(url_for('main.main_menu_editor', website_url=website_url))

    # 메뉴 타입에 따라 템플릿 결정
    template_mapping = {
        'list': 'list_editor.html',
        'gallery': 'gallery_editor.html',
        'home': 'home_editor.html'
    }

    template = template_mapping.get(main_menu.type)

    if template:
        return render_template(template, website_data=user_website_data, menu=main_menu, content=main_menu.content, body_class='edit-mode', form=form)
    else:
        return "Menu type not found", 404


@bp.route('/<string:website_url>/<string:menu_name>/editor', methods=['GET', 'POST'])
@login_required
def menu_editor(website_url, menu_name):
    form = MenuEditForm()

    # Get website and menu data
    user_website_data = UserWebsiteData.query.filter_by(website_url=website_url).first_or_404()
    menu = Menu.query.filter_by(website_id=user_website_data.id, name=menu_name).first_or_404()

    if form.validate_on_submit():
        # Save edited content for the selected menu
        content = form.content.data
        if content:
            menu.content = content  # 메뉴의 내용을 저장
            # 메뉴의 순서는 건드리지 않음
            db.session.commit()
            flash('Changes saved!', 'success')

        return redirect(url_for('main.menu_editor', website_url=website_url, menu_name=menu_name))

    # 메뉴의 타입에 따라 다른 템플릿을 사용
    template_mapping = {
        'list': 'list_editor.html',
        'gallery': 'gallery_editor.html',
        'home': 'home_editor.html'
    }

    template = template_mapping.get(menu.type)

    if template:
        return render_template(template, website_data=user_website_data, menu=menu, content=menu.content, body_class='edit-mode', form=form)
    else:
        return "Menu type not found", 404



@bp.route('/<string:website_url>/edit-setup', methods=['GET', 'POST'])
@login_required
def edit_setup(website_url):
    form = WebsiteSetupForm()

    user_website_data = UserWebsiteData.query.filter_by(user_id=current_user.id, website_url=website_url).first()
    menus = Menu.query.filter_by(website_id=user_website_data.id).order_by(Menu.order).all()

    if form.validate_on_submit():
        website_name = form.website_name.data if form.website_name.data else user_website_data.website_name

        # 웹사이트 이름이 변경된 경우 업데이트
        if user_website_data.website_name != website_name:
            user_website_data.website_name = website_name

        # 메뉴 데이터 처리
        submitted_menu_orders = []
        index = 1
        while True:
            menu_name_field = f'menu_name_{index}'
            menu_type_field = f'menu_type_{index}'
            menu_order_field = f'menu_order_{index}'
            menu_name = request.form.get(menu_name_field)
            menu_type = request.form.get(menu_type_field)
            menu_order = request.form.get(menu_order_field)

            if menu_name and menu_type and menu_order:
                menu_order = int(menu_order)
                submitted_menu_orders.append(menu_order)
                menu = Menu.query.filter_by(website_id=user_website_data.id, order=menu_order).first()

                if menu:
                    # 홈 메뉴의 경우 이름 수정 가능, 순서는 수정 불가
                    if menu.order == 1:
                        menu.name = menu_name  # 이름은 수정 가능
                        menu.type = menu_type  # 타입 수정 가능

                    else:
                        # 홈 메뉴가 아닌 경우 이름과 타입 모두 수정 가능
                        menu.name = menu_name
                        menu.type = menu_type
                        menu.order = menu_order

                    # 메뉴 순서는 이미 menu_order로 설정되어 있으므로 변경할 필요 없음
                else:
                    # 새로운 메뉴 추가
                    new_menu = Menu(
                        name=menu_name,
                        type=menu_type,
                        order=menu_order,
                        website_id=user_website_data.id
                    )
                    db.session.add(new_menu)
                index += 1
            else:
                break

        # 기존 메뉴 중 제출되지 않은 메뉴 삭제
        existing_menus = Menu.query.filter_by(website_id=user_website_data.id).all()
        for menu in existing_menus:
            if menu.order not in submitted_menu_orders:
                # order가 1인 메뉴는 삭제하지 않음
                if menu.order != 1:
                    db.session.delete(menu)

        db.session.commit()

        flash('Website updated successfully!', 'success')
        return redirect(url_for('main.user_website', website_url=user_website_data.website_url))

    else:
        form.website_name.data = user_website_data.website_name

    return render_template('setup.html', form=form, website_data=user_website_data, menus=menus, enumerate=enumerate)




@bp.route('/save-home-content', methods=['POST'])
@login_required
def save_home_content():
    content = request.form['content']  # CKEditor에서 전송된 데이터
    user_website_data = UserWebsiteData.query.filter_by(user_id=current_user.id).first()

    if user_website_data:
        user_website_data.home_content = content  # CKEditor로 수정된 내용 저장
        db.session.commit()
        flash('Home content updated successfully!', 'success')
    else:
        flash('Error updating content.', 'danger')

    return redirect(url_for('main.user_website', website_url=user_website_data.website_url))


@bp.route('/<string:menu_name>/edit-content', methods=['POST'])
@login_required
def save_menu_content(menu_name):
    content = request.form['content']  # CKEditor에서 전송된 데이터
    user_website_data = UserWebsiteData.query.filter_by(user_id=current_user.id).first()

    if user_website_data:
        # 정렬된 메뉴 가져오기
        menus = Menu.query.filter_by(website_id=user_website_data.id).order_by(Menu.order).all()    
        
        if menu:
            # 메뉴의 컨텐츠를 업데이트
            menu.content = content  # CKEditor로 수정된 메뉴 컨텐츠 저장
            db.session.commit()
            flash(f'{menu.name} content updated successfully!', 'success')
        else:
            flash(f'Menu {menu_name} not found.', 'danger')
    else:
        flash('Error updating content.', 'danger')

    return redirect(url_for('main.user_website', website_url=user_website_data.website_url))


# 파일 확장자 허용 검사 함수
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    if 'upload' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['upload']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 파일 유효성 검사
    if file and allowed_file(file.filename):
        # 파일명을 안전하게 변경
        filename = secure_filename(file.filename)
        # 파일 저장 경로 설정
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)
        
        # 파일 저장
        try:
            file.save(file_path)
            current_app.logger.info(f'File successfully uploaded to {file_path}')
        except Exception as e:
            current_app.logger.error(f'File save failed: {e}')
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500

        # 저장된 파일의 URL 생성
        file_url = url_for('static', filename=f'uploads/{filename}', _external=True)

        # 업로드 성공 시 이미지 URL 반환
        return jsonify({'url': file_url}), 200

    return jsonify({'error': 'Invalid file type'}), 400





@bp.route('/save-edits', methods=['POST'])
@login_required
def save_edits():
    # CSRF 토큰을 헤더로 전달받을 경우 검증해야 합니다
    data = request.get_json()
    content = data.get('content')
    menu_id = data.get('menu_id')

    if not content or not menu_id:
        return jsonify({'status': 'error', 'message': 'Missing content or menu_id'}), 400

    # 메뉴를 DB에서 조회하고 현재 로그인한 사용자의 권한을 확인합니다
    menus = Menu.query.filter_by(website_id=user_website_data.id).order_by(Menu.order).all()

    

    if menu and menu.website.user_id == current_user.id:
        menu.content = content  # 콘텐츠를 업데이트
        db.session.commit()
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Unauthorized or content not found'}), 403

