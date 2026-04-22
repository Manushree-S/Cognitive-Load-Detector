from django.shortcuts import render, redirect
from .models import TestResult
import time
from django.contrib.auth.decorators import login_required


# 🔥 QUESTION BANK
questions = [
    {"q": "2 + 2 = ?", "options": ["3", "4", "5"], "answer": "4"},
    {"q": "5 * 3 = ?", "options": ["15", "10", "20"], "answer": "15"},
    {"q": "10 - 4 = ?", "options": ["6", "5", "7"], "answer": "6"},
    {"q": "12 / 4 = ?", "options": ["2", "3", "4"], "answer": "3"},
    {"q": "9 + 6 = ?", "options": ["14", "15", "16"], "answer": "15"},
    {"q": "7 * 2 = ?", "options": ["12", "14", "16"], "answer": "14"},
    {"q": "15 - 5 = ?", "options": ["5", "10", "15"], "answer": "10"},
    {"q": "3 * 3 = ?", "options": ["6", "9", "12"], "answer": "9"},
]


# 🧠 STEP 1: USER TYPE SELECTION
@login_required
def select_user_type(request):
    if request.method == "POST":
        user_type = request.POST.get('user_type', 'normal')

        # safety check
        if user_type not in ['normal', 'adhd', 'dyslexia']:
            user_type = 'normal'

        request.session['user_type'] = user_type
        return redirect('/test/')

    return render(request, 'user_type.html')


# 🧠 STEP 2: QUIZ VIEW
@login_required
def test_page(request):

    user_type = request.session.get('user_type', 'normal')

    if request.method == "POST":

        # ⏱ TIME CALCULATION
        start_time = float(request.POST.get('start_time', time.time()))
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)

        # 🖱 CURSOR + IDLE (SAFE PARSING)
        try:
            idle_time = float(request.POST.get('idle_time', 0))
        except:
            idle_time = 0

        try:
            movement_count = int(request.POST.get('movement_count', 0))
        except:
            movement_count = 0

        # 🔥 DEBUG (CHECK TERMINAL)
        print("\n===== DEBUG DATA =====")
        print("User Type:", user_type)
        print("Cursor Movements:", movement_count)
        print("Idle Time:", idle_time)
        print("======================\n")

        errors = 0
        total_questions = len(questions)

        # ✅ CHECK ANSWERS
        for i, q in enumerate(questions):
            user_ans = request.POST.get(f"q{i+1}")
            if user_ans is None or user_ans != q["answer"]:
                errors += 1

        # 🎯 ACCURACY
        accuracy = ((total_questions - errors) / total_questions) * 100

        # 🧠 COGNITIVE LOAD CALCULATION
        load = calculate_cognitive_load(
            user_type,
            accuracy,
            time_taken,
            errors,
            idle_time,
            movement_count
        )

        # 💾 SAVE TO DATABASE
        TestResult.objects.create(
            user=request.user,
            user_type=user_type,
            time_taken=time_taken,
            errors=errors,
            load_level=load,
            cursor_movements=movement_count,
            idle_time=idle_time
        )

        return render(request, 'result.html', {
            'load': load,
            'errors': errors,
            'time': time_taken,
            'accuracy': round(accuracy, 2),
            'user_type': user_type,
            'idle_time': idle_time,
            'movements': movement_count
        })

    return render(request, 'test.html', {
        'questions': questions,
        'start_time': time.time()
    })


# 🧠 CORE LOGIC FUNCTION (VERY IMPORTANT)
def calculate_cognitive_load(user_type, accuracy, time_taken, errors, idle_time, movement_count):

    # 🔥 ADHD LOGIC (hyperactivity + distraction)
    if user_type == "adhd":
        if movement_count > 300 or idle_time > 12 or errors > 3:
            return "High"
        elif movement_count > 150 or errors >= 2:
            return "Medium"
        else:
            return "Low"

    # 🔥 DYSLEXIA LOGIC (slow reading + accuracy issues)
    elif user_type == "dyslexia":
        if accuracy < 40 or time_taken > 90:
            return "High"
        elif accuracy < 70 or time_taken > 60:
            return "Medium"
        else:
            return "Low"

    # 🔥 NORMAL USERS
    else:
        if accuracy < 50 or time_taken > 60:
            return "High"
        elif accuracy < 80 or time_taken > 40:
            return "Medium"
        else:
            return "Low"


# 📊 STEP 3: DASHBOARD VIEW
@login_required
def dashboard(request):
    results = TestResult.objects.filter(user=request.user).order_by('id')

    attempts = list(range(1, len(results) + 1))
    errors = [r.errors for r in results]
    times = [r.time_taken for r in results]
    movements = [r.cursor_movements for r in results]
    idle_times = [r.idle_time for r in results]

    total_questions = len(questions)

    accuracies = [
        round(((total_questions - r.errors) / total_questions) * 100, 2)
        for r in results
    ]

    return render(request, 'dashboard.html', {
        'results': results,
        'attempts': attempts,
        'errors': errors,
        'times': times,
        'accuracies': accuracies,
        'movements': movements,
        'idle_times': idle_times
    })