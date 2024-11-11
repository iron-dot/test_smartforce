from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartforce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = False
db = SQLAlchemy(app)

# 데이터베이스 모델 설정
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    phone = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    consent_given = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)  # 관리자 여부 확인 필드

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_amount = db.Column(db.Float, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

# 무작위 쿠폰 코드 생성 함수
def generate_random_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# 특별 쿠폰과 일반 쿠폰 생성 함수
def create_coupons():
    # 최초의 10인용 특별 쿠폰 (2000 포인트)
    for _ in range(10):
        code = generate_random_code()
        coupon = Coupon(code=code, discount_amount=2000)
        db.session.add(coupon)

    # 최초의 90인용 일반 쿠폰 (1000 포인트)
    for _ in range(90):
        code = generate_random_code()
        coupon = Coupon(code=code, discount_amount=1000)
        db.session.add(coupon)

    db.session.commit()
    print("쿠폰 생성 완료.")

# 기본 홈 페이지 라우트
@app.route('/')
def index():
    return render_template('index.html')

# 회원가입
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        consent_given = 'consent' in request.form

        # 이메일 중복 확인
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('이미 사용 중인 이메일입니다. 다른 이메일을 입력하세요.', 'danger')
            return redirect(url_for('register'))

        if not consent_given:
            flash('개인정보 수집 및 이용에 동의해야 합니다.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, phone=phone, password=hashed_password, consent_given=consent_given)
        db.session.add(new_user)
        db.session.commit()
        
        flash('회원가입이 완료되었습니다.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# 로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin  # 관리자 여부 세션에 저장
            flash('로그인 성공!', 'success')
            
            # 관리자인 경우 관리자 대시보드로 리디렉션
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('로그인 실패. 이메일과 비밀번호를 확인하세요.', 'danger')
    return render_template('login.html')

# 쿠폰 적용
@app.route('/apply_coupon', methods=['POST'])
def apply_coupon():
    code = request.form['coupon_code']
    coupon = Coupon.query.filter_by(code=code, is_used=False).first()
    
    if coupon:
        flash(f'{coupon.discount_amount} 포인트가 적립되었습니다!', 'success')
        coupon.is_used = True
        db.session.commit()
    else:
        flash('유효하지 않은 쿠폰 코드입니다.', 'danger')
    return redirect(url_for('dashboard'))

# 관리자 대시보드
@app.route('/admin_dashboard')
def admin_dashboard():
    # 관리자가 아닌 경우 접근 제한
    if not session.get('is_admin'):
        flash('관리자 권한이 필요합니다.', 'danger')
        return redirect(url_for('login'))
    
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

# 사용자 대시보드
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('로그인 후 이용 가능합니다.', 'danger')
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# 로그아웃
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('login'))
# 예시 라우트 설정
@app.route('/service_info')
def service_info():
    return render_template('service_info.html')  # 서비스 안내 페이지

@app.route('/some_auction_route')
def some_auction_route():
    return render_template('auction.html')  # 경매 페이지

@app.route('/rentals')
def rentals():
    return render_template('rentals.html')  # 대여 페이지

# 초기 실행 시 관리자 계정 및 쿠폰 생성
with app.app_context():
    db.create_all()

    # 관리자 계정 생성
    if not User.query.filter_by(email="ruin1234@gmail.com").first():
        admin = User(
            username="Ruin",
            email="ruin1234@gmail.com",
            phone="06256748964",
            password=generate_password_hash("superintelligence"),
            consent_given=True,
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("관리자 계정 생성 완료.")

    # 쿠폰 생성
    if Coupon.query.count() == 0:  # 쿠폰이 없을 때만 생성
        create_coupons()

# Waitress를 사용하여 서버 실행
if __name__ == '__main__':
    '''from waitress import serve
    serve(app, host="0.0.0.0", port=8000)'''
    app.run(debug=True)
