from flask import Flask, render_template, url_for, redirect, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user  # ignore  # noqa: F401
from datetime import datetime, date, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from sqlalchemy import select, func, desc
import math


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'AdvancedProt'

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db = SQLAlchemy(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  

class Level_ups(db.Model):
    __tablename__ = 'level_ups'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    streak = db.Column(db.Integer, nullable = False, default= 0)
    xp = db.Column(db.Integer, nullable=False, default= 0)
    level = db.Column(db.Integer, nullable=False, default= 0)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class Journal_entry(db.Model):
    __tablename__ = 'journal'
    jId = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    fileName = db.Column(db.String(30), nullable=False, unique=True)
    content = db.Column(db.String)  


class Tasks(db.Model):
    __tablename__ = 'tasks'
    tId = db.Column(db.Integer, primary_key=True)  
    username = db.Column(db.String(20), nullable=False)
    taskName = db.Column(db.String(50), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    taskNotes = db.Column(db.String)
    date = db.Column(db.Date, nullable=False)




class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=80)], render_kw={"placeholder": "Password"})
    
    confirm_password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=80)], render_kw={"placeholder": "Password"})
    
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_name = db.session.execute(
            select(User).filter_by(username=username.data)
        ).scalar_one_or_none()
        
        if existing_user_name:
            raise ValidationError(
                "That username already exists. Please Choose a different One."
            )
        
    def validate_confirm_password(self, confirm_password):
        if confirm_password.data != self.password.data:
            raise ValidationError("Passwords must match.")

        
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=80)], render_kw={"placeholder": "Password"})
    
    submit = SubmitField("Login")



@app.route("/")
@login_required
def index():
    username = current_user.username
    total_task = db.session.execute(select(func.count(Tasks.taskName)).where(Tasks.username == current_user.username)).scalar()
    total_completed_task = db.session.execute(select(func.count(Tasks.taskName)).where(Tasks.username == current_user.username, Tasks.completed == 1)).scalar()
    completion_rate = round(total_completed_task / total_task * 100, 2) if total_task else 0
    xp_calc()
    level_up()
    calculate_streak()

    user_stat = db.session.execute(select(Level_ups).filter_by(username = username)).scalar_one_or_none()

    if not user_stat:
        return 'No such user exists.'

    user_level = user_stat.level
    user_xp = user_stat.xp
    user_streak = user_stat.streak
    xp_next_level =  math.ceil((120 * ((user_level) ** 1.5))) # xp required to cross the current level and reach the next level.
    xp_percentage = math.ceil(user_xp / xp_next_level * 100)
    render_heatmap = heatmap()

    return render_template("index.html",
                            username = username, totalTask = total_task, taskCompleted = total_completed_task, completionRate = completion_rate,
                            userLevel = user_level, userXp = user_xp, userStreak = user_streak, xpNextLevel = xp_next_level, xpPercentage = xp_percentage,
                            heatmapData = render_heatmap)



# a function that will level up the user info everytime the homepage is visited
def level_up():
    stat = db.session.execute(select(Level_ups).where(Level_ups.username == current_user.username)).scalar_one_or_none()

    if stat is None:
        return 'No such user exist to level up.' 

    c_level = stat.level
    c_xp = stat.xp

    xp_req = xp_required(c_level)

    for i in range(1, len(xp_req)):
        if xp_req[i - 1][1] <= c_xp and c_xp < xp_req[i][1]: 
            stat.level = xp_req[i][0]
            db.session.commit()
            return
    
    
        
    if c_xp < xp_req[0][1]:
        stat.level = xp_req[0][0]    
        db.session.commit()
        return


# xp required to level up
def xp_required(level):
    win = 5
    window = [i for i in range(level - win, level + win + 1) if i > 0]
    xp_required_window = [(j, math.ceil((120 * (j ** 1.5)))) for j in window] # each index is a tuple (level, xp required to cross that level)
    return xp_required_window

# Calculate streak whenever user visits homepage cuz that's where streak will be displayed
def calculate_streak():
    completed_dates = db.session.execute(select(Tasks.date).filter_by(username = current_user.username , completed = 1).distinct().order_by(desc(Tasks.date))).scalars().all()
    stat_user = db.session.execute(select(Level_ups).where(Level_ups.username == current_user.username)).scalar_one_or_none()
    if not completed_dates:
        return 0

    
    today = date.today()
    latest = completed_dates[0]
    
    if latest != today and latest != today - timedelta(days=1):
        stat_user.streak = 0
        db.session.commit()
        return 
    
    streak = 0
    expected = latest

    for d in completed_dates:
        
        if d == expected:
            streak += 1
            expected = expected - timedelta(days=1)

        else:
            break

    
    stat_user.streak = streak
    db.session.commit()
    return
    


# This function will increase the xp whenever home page is displayed
def xp_calc():
    xp_stat = db.session.execute(select(Level_ups).filter_by(username = current_user.username)).scalar_one_or_none()
    
    xp = db.session.execute(
        select(func.count())
        .where(
            Tasks.username == current_user.username,
            Tasks.completed == 1
        )
        ).scalar()

    if xp_stat:
        xp_stat.xp = xp * 20
        db.session.commit()


    return
        

def heatmap():
    day_magnitude = db.session.execute(
        select(
            Tasks.date, 
            func.count(Tasks.taskName)
        )
        .where(
            Tasks.username == current_user.username, 
            Tasks.completed == 1
        )
        .group_by(Tasks.date)
    )
    heatmap_data = {str(date): count for date, count in day_magnitude}

    time_delta = 90         #days 
    ordered_data = []       #list of tuples (date, count) ordered by date

    for i in reversed(range(time_delta)):
        date_to_check = (date.today() - timedelta(days = i)).strftime("%Y-%m-%d")
        filtered_date = (date.today() - timedelta(days = i)).strftime("%B %d, %Y")
        count = heatmap_data.get(date_to_check, 0)
        ordered_data.append((date_to_check, count, filtered_date))
        
    return ordered_data



@app.route("/api/index/graph")
@login_required
def graph_data():
    completion_rates = []
    tasks_assigned = []
    tasks_completed = []
    username = current_user.username
    total_dates = db.session.execute(select(Tasks.date).filter_by(username = username).distinct()).scalars().all()


    for datee in  total_dates:
        assigned_task =  db.session.execute(select(func.count(Tasks.taskName)).where(Tasks.username == current_user.username, Tasks.date == datee)).scalar()
        completed_task = db.session.execute(select(func.count(Tasks.taskName)).where(Tasks.username == current_user.username, Tasks.completed == 1, Tasks.date == datee)).scalar()
        completion_rates.append((completed_task/assigned_task) * 100)
        tasks_assigned.append(assigned_task)
        tasks_completed.append(completed_task)

    label_dates = [f"{d.day}/{d.month}" for d in total_dates]

    return jsonify({"completionRate": completion_rates, "dateLabel": label_dates, "tasksAssigned": tasks_assigned, "tasksCompleted": tasks_completed}), 200


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.execute(
            select(User).filter_by(username=form.username.data)
        ).scalar_one_or_none()
        
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('index'))
        
        # This runs if user doesn't exist OR password is wrong
        flash('Invalid username or password', 'error')

    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    print("Form submitted:", form.is_submitted())
    print("Form valid:", form.validate_on_submit())
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_password)
        user_stat = Level_ups(username = form.username.data, streak = 0, xp = 0, level = 1)
        db.session.add(new_user)
        db.session.add(user_stat)
        db.session.commit()
        print("User created!")
        return redirect(url_for('login'))

    return render_template("register.html", form=form)


# This is the main task page renderer. 
@app.route("/tasks")
@login_required 
def tasks():

    current_date = datetime.now().strftime("%B %d, %Y")
    taskList = db.session.execute(select(Tasks.taskName).filter_by(username=current_user.username, date=date.today())).scalars().all()
    areCompleted = db.session.execute(select(Tasks.completed).filter_by(username = current_user.username, date = date.today())).scalars().all()
    taskIds = db.session.execute(select(Tasks.tId).filter_by(username=current_user.username, date=date.today())).scalars().all()
    task_ref = dict(zip(taskIds, zip(taskList, areCompleted)))

    task_pending = db.session.execute(select(func.count(Tasks.taskName)).where(Tasks.username == current_user.username, Tasks.date == date.today())).scalar()
    task_completed = db.session.execute(select(func.count(Tasks.taskName)).where(Tasks.username == current_user.username, Tasks.date == date.today(), Tasks.completed == 1)).scalar()
    
    return render_template("tasks.html", current_date=current_date, taskInfo = task_ref, taskPending = task_pending, taskCompleted = task_completed, taskIds=taskIds)



# This is how we mark a task status and make changes in the database accordingly.
@app.route("/api/task/mark", methods=["POST"])
@login_required
def task_marking():
    if not request.json or not request.json.get('taskId') or request.json.get('stat') is None:
        return jsonify({"error": "Task Id and Status are required"}), 400

    taskId = request.json.get('taskId')
    taskStatus = request.json.get('stat')

    task = db.session.execute(
        select(Tasks).filter_by(tId = taskId)
    ).scalar_one_or_none()

    if task and date.today() == task.date:
        task.completed = bool(taskStatus)
        db.session.commit()
        return '', 204

    return jsonify({"error": "No task to complete"})


# This is how we update the task completion status. How many tasks are completed / How many are pending.
@app.route("/api/task/completion")
@login_required
def task_completion_update():
    

    date_filterr = request.args.get("date")
    if date_filterr == '':
        date_filterr = date.today()

    task_pending = db.session.execute(select(func.count(Tasks.taskName)).where(Tasks.username == current_user.username, Tasks.date == date_filterr)).scalar()
    task_completed = db.session.execute(select(func.count(Tasks.taskName)).where(Tasks.username == current_user.username, Tasks.date == date_filterr, Tasks.completed == 1)).scalar()


    return jsonify({"tPending": task_pending, "tCompleted": task_completed}), 200


# This is how we create a new task.
@app.route("/api/task/create", methods=["POST"])
@login_required
def create_task():

    if not request.json or not request.json.get('task'):
        return jsonify({"error": "Task name is required"}), 400
    
    
    taskName = request.json.get('task').strip()
    if len(taskName) > 50:
        return jsonify({"error": "Task name too long"}), 400

    username = current_user.username
    newTask = Tasks(username=username, taskName = taskName, taskNotes='', date=date.today())

    db.session.add(newTask)
    db.session.commit()

    display_date = (datetime.strptime(str(date.today()), "%Y-%m-%d").date()).strftime("%B %d, %Y")
    taskList = db.session.execute(select(Tasks.taskName).filter_by(username=current_user.username, date=date.today())).scalars().all()
    areCompleted = db.session.execute(select(Tasks.completed).filter_by(username = current_user.username, date = date.today())).scalars().all()
    taskIds = db.session.execute(select(Tasks.tId).filter_by(username=current_user.username, date=date.today())).scalars().all()
    task_ref = dict(zip(taskIds, zip(taskList, areCompleted)))

    return render_template("_task_list_update.html", taskInfo = task_ref, current_date = display_date), 200 # both share same content so no need to be sceptic


# This is how we get the task note of the selected task in the task page.
@app.route("/api/task/notes", methods=["GET"])
@login_required
def get_note():
    tid = request.args.get("id")
    name = request.args.get("name")

    note = db.session.execute(
        select(Tasks.taskNotes).filter_by(tId = tid, taskName=name)
    ).scalar_one_or_none()
    
    if note is not None:
        return jsonify({"note": note}), 200

    else:
        return jsonify({"error": "Issues attaining task note"}), 400


# This is how we update the task note of the selected task.
@app.route("/api/task/update", methods=["POST"])
@login_required
def update_note():

    if not request.json or not request.json.get('content') or not request.json.get('id'):
        return jsonify({"error": "Content & Id is required"}), 400

    tId = request.json.get('id')
    content = request.json.get('content')

    task = db.session.execute(
        select(Tasks).filter_by(tId = tId)
    ).scalar_one_or_none()

    if task:
        task.taskNotes = content
        db.session.commit()
        return '', 204
    
    return jsonify({"error": "No task found"})

# This is how we get tasks filtered by the date selected in the task page.
@app.route("/api/task/date", methods=["POST"])
@login_required
def get_date():
    if not request.json or not request.json.get("date"):
        return {"error": "No date"}, 400
    
    filter_date = request.json.get("date")
    display_date = (datetime.strptime(filter_date, "%Y-%m-%d").date()).strftime("%B %d, %Y")
    taskList = db.session.execute(select(Tasks.taskName).filter_by(username=current_user.username, date=filter_date)).scalars().all()
    areCompleted = db.session.execute(select(Tasks.completed).filter_by(username = current_user.username, date = filter_date)).scalars().all()
    taskIds = db.session.execute(select(Tasks.tId).filter_by(username=current_user.username, date=filter_date)).scalars().all()
    task_ref = dict(zip(taskIds, zip(taskList, areCompleted)))

    return render_template("_task_list_update.html", taskInfo = task_ref, taskIds = taskIds, current_date=display_date) , 200


# This is how we delete a task in the task page.
@app.route("/api/task/delete", methods=["POST"])
@login_required
def delete_task():
    if not request.json or not request.json.get('id'):
        return jsonify({"error": "No task to delete"}), 400

    to_delete = request.json.get("id")
    task_to_delete = db.session.execute(
        select(Tasks).filter_by(tId = to_delete)
    ).scalar_one_or_none()

    if task_to_delete is None:
        return jsonify({"error": "No task to delete"})

    db.session.delete(task_to_delete)
    db.session.commit()

    filter_date = str(date.today()) if request.json.get("date") == '' else request.json.get("date")

    display_date = (datetime.strptime(filter_date, "%Y-%m-%d").date()).strftime("%B %d, %Y")
    taskList = db.session.execute(select(Tasks.taskName).filter_by(username=current_user.username, date=filter_date)).scalars().all()
    areCompleted = db.session.execute(select(Tasks.completed).filter_by(username = current_user.username, date = filter_date)).scalars().all()
    taskIds = db.session.execute(select(Tasks.tId).filter_by(username=current_user.username, date=filter_date)).scalars().all()
    task_ref = dict(zip(taskIds, zip(taskList, areCompleted)))

    return render_template("_task_list_update.html", taskInfo = task_ref, taskIds = taskIds, current_date=display_date) , 200


# The main journal page renderer.
@app.route("/journal")
@login_required
def journal():
    jlists = db.session.execute(
        select(Journal_entry.fileName).filter_by(username=current_user.username)).scalars().all()

    return render_template('journal.html', jlists=jlists)


# Saving journal content from frontend(js) to database. 
@app.route("/api/journal", methods=["POST"])
@login_required
def save_journal():
    content = request.json.get("content")
    username = current_user.username
    fileName = request.json.get("filename")

    user_files = db.session.execute(
        select(Journal_entry.fileName).filter_by(username=username)
    ).scalars().all()

    # If an file with the name exists, update it
    if fileName in user_files:
        journal_entry = db.session.execute(
            select(Journal_entry).filter_by(fileName=fileName)
        ).scalar_one()
        journal_entry.content = content
        db.session.commit()
        return '', 204
        
    # otherwise create a new entry
    journal_entry = Journal_entry(username=username, fileName=fileName, content=content)
    db.session.add(journal_entry)
    db.session.commit()


    
    return '', 204


# Sending journal content to frontend(js)
@app.route("/api/journal/get", methods=["GET"])
@login_required
def get_journal():
    username = current_user.username
    fileName = request.args.get("filename")
    
    content = db.session.execute(
        select(Journal_entry.content).filter_by(username=username, fileName=fileName)
    ).scalar_one_or_none()
    
    return jsonify({"content": content}) if content else jsonify({"content": None})



# this is how we create a new journal file.
@app.route("/api/journal/create", methods=["POST"])
@login_required
def create_file():
    fName = request.json.get("filename")
    username = current_user.username

    existingFile = db.session.execute(
        select(Journal_entry.fileName).filter_by(username=username, fileName=fName)
    ).scalar_one_or_none()

    if existingFile:
        return jsonify({"error": "File with this name already exists."}), 400

    newFile = Journal_entry(username=username, fileName=fName, content="")
    db.session.add(newFile)
    db.session.commit()
    
    journal_list = db.session.execute(select(Journal_entry.fileName).filter_by(username = username)).scalars().all()


    return render_template("journal_update.html", jLists = journal_list), 200



# this is how we delete a journal file.
@app.route("/api/journal/delete", methods=["POST"])
@login_required
def delete_file():
    fName = request.json.get("filename")
    username = current_user.username

    file_to_delete = db.session.execute(
        select(Journal_entry).filter_by(username=username, fileName=fName)
    ).scalar_one_or_none()

    if not file_to_delete:
        return jsonify({"error": "File not found."}), 404

    db.session.delete(file_to_delete)
    db.session.commit()

    journal_list = db.session.execute(select(Journal_entry.fileName).filter_by(username = username)).scalars().all()


    return render_template("journal_update.html", jLists = journal_list), 200



# The webpage stays in debug mode so that we can make changes and see them without restarting the server.
if __name__ == '__main__':
    app.run(debug=True)