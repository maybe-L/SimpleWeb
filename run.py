from flask import Flask, render_template
from app import create_app

app = create_app()  # create_app 함수를 호출하여 앱 생성

if __name__ == '__main__':
    app.run(debug=True)
