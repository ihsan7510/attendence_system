from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Teacher, Class, Subject, Student, Attendance
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Teacher.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        teacher = Teacher.query.filter_by(email=email).first()
        
        if teacher and check_password_hash(teacher.password_hash, password):
            login_user(teacher)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)


@app.route('/classes', methods=['GET', 'POST'])
@login_required
def manage_classes():
    if request.method == 'POST':
        class_name = request.form.get('name')
        if class_name:
            existing_class = Class.query.filter_by(name=class_name).first()
            if existing_class:
                flash('Class already exists!', 'warning')
            else:
                new_class = Class(name=class_name)
                db.session.add(new_class)
                db.session.commit()
                flash('Class added successfully!', 'success')
        else:
            flash('Class name cannot be empty.', 'danger')
        return redirect(url_for('manage_classes'))
    
    classes = Class.query.all()
    return render_template('classes.html', classes=classes)

@app.route('/delete_class/<int:class_id>')
@login_required
def delete_class(class_id):
    class_to_delete = Class.query.get_or_404(class_id)
    db.session.delete(class_to_delete)
    db.session.commit()
    flash('Class deleted successfully!', 'success')
    return redirect(url_for('manage_classes'))

@app.route('/subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    if request.method == 'POST':
        subject_name = request.form.get('name')
        class_id = request.form.get('class_id')
        
        if subject_name and class_id:
            new_subject = Subject(name=subject_name, class_id=class_id)
            db.session.add(new_subject)
            db.session.commit()
            flash('Subject added successfully!', 'success')
        else:
            flash('All fields are required.', 'danger')
        return redirect(url_for('manage_subjects'))

    subjects = Subject.query.join(Class).all()
    classes = Class.query.all()
    return render_template('subjects.html', subjects=subjects, classes=classes)

@app.route('/delete_subject/<int:subject_id>')
@login_required
def delete_subject(subject_id):
    subject_to_delete = Subject.query.get_or_404(subject_id)
    db.session.delete(subject_to_delete)
    db.session.commit()
    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('manage_subjects'))

@app.route('/students', methods=['GET', 'POST'])
@login_required
def manage_students():
    if request.method == 'POST':
        name = request.form.get('name')
        roll_number = request.form.get('roll_number')
        class_id = request.form.get('class_id')
        
        if name and roll_number and class_id:

            existing_student = Student.query.filter_by(roll_number=roll_number, class_id=class_id).first()
            if existing_student:
                flash(f'Roll number {roll_number} already exists in this class!', 'warning')
            else:
                new_student = Student(name=name, roll_number=roll_number, class_id=class_id)
                db.session.add(new_student)
                db.session.commit()
                flash('Student added successfully!', 'success')
        else:
            flash('All fields are required.', 'danger')
        return redirect(url_for('manage_students'))


    class_filter = request.args.get('class_id')
    if class_filter:
        students = Student.query.filter_by(class_id=class_filter).join(Class).all()
    else:
        students = Student.query.join(Class).all()
        
    classes = Class.query.all()
    return render_template('students.html', students=students, classes=classes, selected_class=class_filter)

@app.route('/delete_student/<int:student_id>')
@login_required
def delete_student(student_id):
    student_to_delete = Student.query.get_or_404(student_id)
    db.session.delete(student_to_delete)
    db.session.commit()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('manage_students'))

@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    if request.method == 'POST':
        class_id = request.form.get('class_id')
        subject_id = request.form.get('subject_id')
        date_str = request.form.get('date')
        
        if not (class_id and subject_id and date_str):
            flash('Missing information.', 'danger')
            return redirect(url_for('mark_attendance'))
            
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        

        existing = Attendance.query.filter_by(class_id=class_id, subject_id=subject_id, date=date_obj).first()
        if existing:
            flash('Attendance already marked for this class, subject, and date.', 'warning')
            return redirect(url_for('mark_attendance'))

        students = Student.query.filter_by(class_id=class_id).all()
        for student in students:
            status = request.form.get(f'status_{student.id}')
            if status:
                attendance = Attendance(
                    student_id=student.id,
                    class_id=class_id,
                    subject_id=subject_id,
                    date=date_obj,
                    status=status
                )
                db.session.add(attendance)
        
        db.session.commit()
        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('dashboard'))


    class_id = request.args.get('class_id')
    subject_id = request.args.get('subject_id')
    date_str = request.args.get('date')
    
    students = []
    already_marked = False
    
    if class_id and subject_id and date_str:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        existing = Attendance.query.filter_by(class_id=class_id, subject_id=subject_id, date=date_obj).first()
        if existing:
            already_marked = True
            flash('Attendance has already been marked for this selection.', 'info')
        else:
            students = Student.query.filter_by(class_id=class_id).all()
            if not students:
                flash('No students found in this class.', 'warning')

    classes = Class.query.all()
    subjects = Subject.query.join(Class).all()
    
    return render_template('attendance.html', 
                         classes=classes, 
                         subjects=subjects, 
                         students=students, 
                         already_marked=already_marked,
                         selected_class=class_id,
                         selected_subject=subject_id,
                         selected_date=date_str)

@app.route('/reports')
@login_required
def view_reports():
    class_id = request.args.get('class_id')
    subject_id = request.args.get('subject_id')
    
    report_data = []
    total_days = 0
    dates = []
    
    if class_id and subject_id:

        dates_query = db.session.query(Attendance.date).filter_by(
            class_id=class_id, subject_id=subject_id
        ).distinct().order_by(Attendance.date).all()
        dates = [d[0] for d in dates_query]
        total_days = len(dates)
        

        students = Student.query.filter_by(class_id=class_id).order_by(Student.roll_number).all()
        
        for student in students:
            present_count = Attendance.query.filter_by(
                student_id=student.id, class_id=class_id, subject_id=subject_id, status='Present'
            ).count()
            
            percentage = (present_count / total_days * 100) if total_days > 0 else 0
            
            report_data.append({
                'student': student,
                'present': present_count,
                'total': total_days,
                'percentage': round(percentage, 2)
            })

    classes = Class.query.all()
    subjects = Subject.query.join(Class).all()
    
    return render_template('reports.html', 
                         classes=classes, 
                         subjects=subjects,
                         report_data=report_data,
                         dates=dates,
                         selected_class=class_id,
                         selected_subject=subject_id)

@app.route('/teachers', methods=['GET', 'POST'])
@login_required
def manage_teachers():
    if not current_user.is_admin:
        flash('Access denied. Admin rights required.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if name and email and password:
            existing_teacher = Teacher.query.filter_by(email=email).first()
            if existing_teacher:
                flash('Email already registered!', 'warning')
            else:
                hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
                new_teacher = Teacher(name=name, email=email, password_hash=hashed_pw, is_admin=False)
                db.session.add(new_teacher)
                db.session.commit()
                flash('Teacher added successfully!', 'success')
        else:
            flash('All fields are required.', 'danger')
        return redirect(url_for('manage_teachers'))

    teachers = Teacher.query.all()
    return render_template('teachers.html', teachers=teachers)

@app.route('/edit_teacher/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
def edit_teacher(teacher_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
        
    teacher = Teacher.query.get_or_404(teacher_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if name and email:

            existing = Teacher.query.filter_by(email=email).first()
            if existing and existing.id != teacher.id:
                 flash('Email already registered by another teacher!', 'warning')
            else:
                teacher.name = name
                teacher.email = email
                if password:
                    teacher.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
                
                db.session.commit()
                flash('Teacher details updated successfully!', 'success')
                return redirect(url_for('manage_teachers'))
        else:
            flash('Name and Email are required.', 'danger')
            
    return render_template('edit_teacher.html', teacher=teacher)

@app.route('/delete_teacher/<int:teacher_id>')
@login_required
def delete_teacher(teacher_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
        
    if teacher_id == current_user.id:
        flash('You cannot delete yourself.', 'warning')
        return redirect(url_for('manage_teachers'))
        
    teacher_to_delete = Teacher.query.get_or_404(teacher_id)
    db.session.delete(teacher_to_delete)
    db.session.commit()
    flash('Teacher deleted successfully!', 'success')
    return redirect(url_for('manage_teachers'))

@app.route('/export')
@login_required
def export_data():
    class_id = request.args.get('class_id')
    subject_id = request.args.get('subject_id')
    
    if not (class_id and subject_id):
        flash('Please select a class and subject to export.', 'warning')
        return redirect(url_for('view_reports'))
        

    query = Attendance.query.filter_by(class_id=class_id, subject_id=subject_id).join(Student).join(Class).join(Subject).order_by(Attendance.date, Student.roll_number).all()
    
    if not query:
        flash('No data found to export.', 'info')
        return redirect(url_for('view_reports', class_id=class_id, subject_id=subject_id))


    import openpyxl
    from io import BytesIO
    from flask import send_file
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Report"
    

    headers = ['Roll No', 'Student Name', 'Class', 'Subject', 'Date', 'Status']
    ws.append(headers)
    
    for record in query:
        row = [
            record.student.roll_number,
            record.student.name,
            record.class_val.name,
            record.subject.name,
            record.date.strftime('%Y-%m-%d'),
            record.status
        ]
        ws.append(row)
        
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(output, download_name='attendance_report.xlsx', as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not Teacher.query.filter_by(email='teacher@example.com').first():
            hashed_pw = generate_password_hash('password123', method='pbkdf2:sha256')
            teacher = Teacher(name='Test Teacher', email='teacher@example.com', password_hash=hashed_pw, is_admin=True)
            db.session.add(teacher)
            db.session.commit()

            
    app.run(debug=True)
