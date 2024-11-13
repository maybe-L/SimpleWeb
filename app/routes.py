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
from flask import send_from_directory
import base64
from io import BytesIO
from PIL import Image



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

    user_website_data = UserWebsiteData.query.filter_by(website_url=website_url).first_or_404()
    menu = Menu.query.filter(Menu.website_id == user_website_data.id, Menu.name.ilike(menu_name)).first_or_404()

    return render_template(f'{menu.type}_page.html', menu=menu, website_data=user_website_data)


# 각 메뉴 타입에 대한 기본 템플릿 콘텐츠
default_content_templates = {
    'list': "<hr><p><strong>1. President's Award for Educational Excellence</strong><br><i>Date:</i> June 2022<br><i>Description:</i> Recognized for outstanding academic achievements, maintaining a GPA of 4.0 throughout high school.</p><hr><p><strong>2. National Merit Scholar Finalist</strong><br><i>Date:</i> May 2022<br><i>Description:</i> Selected as a finalist for the National Merit Scholarship Program based on exemplary PSAT scores and academic performance.</p><hr><p><strong>3. 1st Place - Regional Science Fair</strong><br><i>Date:</i> March 2021<br><i>Description:</i> Awarded first place in the regional science fair for a project on renewable energy solutions, which focused on solar panel efficiency improvements.</p><hr><p><strong>4. Student Leadership Award</strong><br><i>Date:</i> April 2022<br><i>Description:</i> Received for demonstrating exceptional leadership as the President of the Student Council, organizing charity events and school improvement projects.</p><hr><p><strong>5. Excellence in Community Service Award</strong><br><i>Date:</i> December 2021<br><i>Description:</i> Awarded for completing over 150 hours of community service, including organizing food drives and volunteering at local shelters.</p><hr><p><strong>6. AP Scholar with Distinction</strong><br><i>Date:</i> July 2022<br><i>Description:</i> Recognized for scoring 5s on five or more AP exams, including AP Biology, AP Chemistry, and AP Calculus.</p><hr><p><strong>7. Varsity Soccer MVP</strong><br><i>Date:</i> October 2021<br><i>Description:</i> Named Most Valuable Player for leading the varsity soccer team to victory in the state championships.</p><hr><p><strong>8. Honorable Mention - National Art Competition</strong><br><i>Date:</i> June 2020<br><i>Description:</i> Received honorable mention for a painting submitted to a national-level art competition focused on cultural heritage.</p><hr><p><strong>9. Math Olympiad Silver Medalist</strong><br><i>Date:</i> February 2021<br><i>Description:</i> Earned a silver medal in the National Math Olympiad for solving complex problems in algebra and geometry.</p><hr>",
    'gallery': '<hr><figure class="image"><img style="aspect-ratio:2100/1500;" src=\'http://127.0.0.1:5000/static/uploads/painting.jpg\' width=\'2100\' height=\'1500\'></figure><p><strong>Title:</strong> <i>Reflections of Identity</i></p><p><i>Medium:</i> Oil on Canvas<br><i>Dimensions:</i> 18 x 24 inches<br><i>Year:</i> 2023</p><hr><figure class="media"><oembed url=\'https://youtu.be/0GsajWIF3ws\'></oembed></figure><p><strong>Title:</strong> <i>Modern Dance Ensemble - \'</i><strong>Swan Lake</strong><i>\'</i><br><i>Date:</i> February 2023<br><i>Description:</i> A modern dance piece performed as part of a collaborative group. Emphasized group dynamics, synchronization, and expressive movement.</p><hr>',
    'home': "<p><img src=\"http://127.0.0.1:5000/static/uploads/student.jpg\"> Hello, my name is Emily White. I am a diligent student who consistently strives to achieve both personal and academic growth. Throughout high school, I maintained strong relationships with my classmates, often serving as a mediator in group projects to ensure collaboration and harmony. As the president of the student council, I led initiatives such as organizing charity events and improving school facilities, which allowed me to develop strong leadership skills. Additionally, my commitment to community service is reflected in my volunteer work at local shelters, where I organized food drives and helped create after-school programs for underprivileged children. These experiences have deepened my desire to contribute to society and shaped my strong sense of responsibility and compassion for others.</p>"
}


@bp.route('/<string:website_url>/editor', methods=['GET', 'POST'])
@login_required
def main_menu_editor(website_url):
    # 웹사이트 데이터 가져오기
    user_website_data = UserWebsiteData.query.filter_by(website_url=website_url).first_or_404()
    main_menu = Menu.query.filter_by(website_id=user_website_data.id, order=1).first()

    form = MenuEditForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            content = form.content.data
            if content:
                main_menu.content = content
                db.session.commit()
                flash('Main page content saved!', 'success')
            else:
                flash('No content provided.', 'danger')
        return redirect(url_for('main.main_menu_editor', website_url=website_url))

    content = main_menu.content if main_menu.content and main_menu.content != 'None' else default_content_templates.get(main_menu.type, '')
    form.content.data = content if content != 'None' else ''

    # 템플릿 결정
    template_mapping = {
        'list': 'list_editor.html',
        'gallery': 'gallery_editor.html',
        'home': 'home_editor.html'
    }
    template = template_mapping.get(main_menu.type)

    if template:
        return render_template(
            template, 
            website_data=user_website_data, 
            menu=main_menu, 
            content=form.content.data, 
            body_class='edit-mode', 
            form=form,
            current_menu_order=main_menu.order  # current_menu_order 전달
        )
    else:
        return "Menu type not found", 404

@bp.route('/<string:website_url>/<string:menu_name>/editor', methods=['GET', 'POST'])
@login_required
def menu_editor(website_url, menu_name):
    form = MenuEditForm()
    user_website_data = UserWebsiteData.query.filter_by(website_url=website_url).first_or_404()
    menu = Menu.query.filter(Menu.website_id == user_website_data.id, Menu.name.ilike(menu_name)).first_or_404()

    if form.validate_on_submit():
        content = form.content.data
        if content:
            menu.content = content
            db.session.commit()
            flash('Changes saved!', 'success')
        return redirect(url_for('main.menu_editor', website_url=website_url, menu_name=menu_name))

    content = menu.content if menu.content and menu.content != 'None' else default_content_templates.get(menu.type, '')
    form.content.data = content if content != 'None' else ''

    template_mapping = {
        'list': 'list_editor.html',
        'gallery': 'gallery_editor.html',
        'home': 'home_editor.html'
    }
    template = template_mapping.get(menu.type)

    if template:
        return render_template(
            template, 
            website_data=user_website_data, 
            menu=menu, 
            content=form.content.data, 
            body_class='edit-mode', 
            form=form,
            current_menu_order=menu.order  # current_menu_order 전달
        )
    else:
        return "Menu type not found", 404
    

@bp.route('/<string:website_url>/edit-setup', methods=['GET', 'POST'])
@login_required
def edit_setup(website_url):
    form = WebsiteSetupForm()

    # 현재 유저의 웹사이트 데이터를 가져옴
    user_website_data = UserWebsiteData.query.filter_by(user_id=current_user.id, website_url=website_url).first()

    # 메뉴 데이터를 order 값으로 정렬하여 가져옴
    menus = Menu.query.filter_by(website_id=user_website_data.id).order_by(Menu.order).all()

    if form.validate_on_submit():
        website_name = form.website_name.data if form.website_name.data else user_website_data.website_name
        if user_website_data.website_name != website_name:
            user_website_data.website_name = website_name

        # 메뉴 데이터 처리
        submitted_menu_orders = []
        duplicate_order_error = False  # 중복된 오더 값 확인용 플래그
        index = 1

        while True:
            # 각 필드에서 데이터를 가져옴
            menu_name_field = f'menu_name_{index}'
            menu_type_field = f'menu_type_{index}'
            menu_order_field = f'menu_order_{index}'
            menu_name = request.form.get(menu_name_field)
            menu_type = request.form.get(menu_type_field)
            menu_order = request.form.get(menu_order_field)

            # 메뉴 정보가 입력된 경우에만 처리
            if menu_name and menu_type and menu_order:
                try:
                    menu_order = int(menu_order)
                except ValueError:
                    flash('Invalid menu order. Please provide a valid number.', 'danger')
                    return redirect(url_for('main.edit_setup', website_url=website_url))

                # 1번 메뉴는 항상 존재해야 하고 order는 1로 고정
                if menu_order == 1:
                    # 1번 메뉴가 이미 있는지 확인
                    main_menu = Menu.query.filter_by(website_id=user_website_data.id, order=1).first()
                    if not main_menu:
                        flash('Main menu could not be set. Please try again.', 'danger')
                        return redirect(url_for('main.edit_setup', website_url=website_url))

                    # 홈 메뉴는 삭제하지 않고 이름과 타입만 수정 가능
                    main_menu.name = menu_name
                    main_menu.type = menu_type
                else:
                    # 중복된 order 값이 있는지 확인
                    if menu_order in submitted_menu_orders:
                        flash(f"Menu order {menu_order} is duplicated. Please provide unique order numbers for each menu.", 'danger')
                        duplicate_order_error = True
                        break
                    else:
                        submitted_menu_orders.append(menu_order)

                    # 기존 메뉴를 가져와 업데이트
                    menu = Menu.query.filter_by(website_id=user_website_data.id, order=menu_order).first()
                    if menu:
                        menu.name = menu_name
                        menu.type = menu_type
                        menu.order = menu_order
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

        # 중복된 오더 값이 있는 경우, 데이터베이스에 변경 사항을 커밋하지 않음
        if duplicate_order_error:
            return redirect(url_for('main.edit_setup', website_url=website_url))

        # 기존 메뉴 중 제출되지 않은 메뉴 삭제 (1번 메뉴는 제외)
        existing_menus = Menu.query.filter_by(website_id=user_website_data.id).all()
        for menu in existing_menus:
            if menu.order not in submitted_menu_orders and menu.order != 1:
                db.session.delete(menu)

        db.session.commit()

        flash('Website updated successfully!', 'success')
        return redirect(url_for('main.user_website', website_url=user_website_data.website_url))

    else:
        form.website_name.data = user_website_data.website_name

    return render_template('setup.html', form=form, website_data=user_website_data, menus=menus, enumerate=enumerate)



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


@bp.route('/upload-thumbnail', methods=['POST'])
@login_required
def upload_thumbnail():
    current_app.logger.info("Thumbnail upload request received.")  # 요청 수신 확인 로그

    try:
        data = request.get_json()
        image_data = data.get('image')
        menu_name = data.get('menu_name')

        if not image_data or not menu_name:
            current_app.logger.error("Invalid data received - image or menu_name is missing.")
            return jsonify({'success': False, 'message': 'Invalid data'}), 400

        # 메뉴 이름을 소문자로 변환하고, 공백을 밑줄로 변경하여 안전한 파일명 생성
        safe_menu_name = menu_name.replace(' ', '_').lower()
        current_app.logger.info(f"Generated safe_menu_name: {safe_menu_name}")  # 디버깅 로그 추가

        # Base64 문자열에서 이미지 데이터 추출
        image_data = image_data.split(",")[1]
        image = Image.open(BytesIO(base64.b64decode(image_data)))

        # 썸네일 저장 경로 설정
        thumbnail_path = os.path.join(current_app.config['THUMBNAIL_FOLDER'], f'thumbnail_{safe_menu_name}.jpg')

        # 썸네일 폴더가 없으면 생성
        if not os.path.exists(current_app.config['THUMBNAIL_FOLDER']):
            os.makedirs(current_app.config['THUMBNAIL_FOLDER'])
            current_app.logger.info(f"Thumbnail folder created at {current_app.config['THUMBNAIL_FOLDER']}")

        # 이미지 저장
        image.save(thumbnail_path, 'JPEG')
        current_app.logger.info(f"Thumbnail saved at {thumbnail_path}")
        return jsonify({'success': True}), 200

    except Exception as e:
        current_app.logger.error(f"Error in upload_thumbnail route: {e}")
        return jsonify({'success': False, 'message': 'Error saving thumbnail'}), 500
