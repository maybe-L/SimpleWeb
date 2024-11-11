from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# 기존 유저 모델
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# 새로운 유저 웹사이트 데이터 모델
class UserWebsiteData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    website_url = db.Column(db.String(255), unique=True, nullable=False)
    website_name = db.Column(db.String(255), nullable=False)
    home_content = db.Column(db.Text, nullable=True)  # 홈 컨텐츠를 저장할 필드 추가
    user = db.relationship('User', backref=db.backref('websites', lazy=True))

    def __repr__(self):
        return f'<Website {self.website_name} owned by {self.user_id}>'

# 메뉴 모델
class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=True)
    content = db.Column(db.Text, nullable=True)  # 에디터에서 저장한 콘텐츠
    html_content = db.Column(db.Text, nullable=True)  # 에디터로 입력된 HTML 전체 내용 저장
    order = db.Column(db.Integer)  # 수동으로 지정할 수 있는 순서
    website_id = db.Column(db.Integer, db.ForeignKey('user_website_data.id'), nullable=False)
    website = db.relationship('UserWebsiteData', backref=db.backref('menus', lazy=True))

    def __repr__(self):
        return f'<Menu {self.name} for Website {self.website_id}>'

# 이미지 모델
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(200), nullable=False)  # 이미지 파일 경로를 저장할 필드
    website_id = db.Column(db.Integer, db.ForeignKey('user_website_data.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=True)  # 메뉴에 연결될 수 있는 이미지
    website = db.relationship('UserWebsiteData', backref=db.backref('images', lazy=True))
    menu = db.relationship('Menu', backref=db.backref('images', lazy=True))  # 메뉴와의 관계 설정

    def __repr__(self):
        return f'<Image {self.image_url} for Website {self.website_id}>'


class Thumbnail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thumbnail_url = db.Column(db.String(200), nullable=False)  # 섬네일 이미지 파일 경로
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)  # 각 메뉴와 연결
    menu = db.relationship('Menu', backref=db.backref('thumbnail', uselist=False))

    def __repr__(self):
        return f'<Thumbnail {self.thumbnail_url} for Menu {self.menu_id}>'
