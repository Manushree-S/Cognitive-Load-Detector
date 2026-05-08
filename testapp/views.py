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


# 🧠 USER TYPE SELECTION
@login_required
def select_user_type(request):

    if request.method == "POST":

        user_type = request.POST.get('user_type', 'normal')

        if user_type not in ['normal', 'adhd', 'dyslexia']:
            user_type = 'normal'

        request.session['user_type'] = user_type

        return redirect('/test/')

    return render(request, 'user_type.html')


# 🧠 QUIZ PAGE
@login_required
def test_page(request):

    user_type = request.session.get('user_type', 'normal')

    if request.method == "POST":

        # ⏱ TIME
        start_time = float(request.POST.get('start_time', time.time()))

        end_time = time.time()

        time_taken = round(end_time - start_time, 2)

        # 🖱 CURSOR + IDLE
        try:
            idle_time = float(request.POST.get('idle_time', 0))
        except:
            idle_time = 0

        try:
            movement_count = int(request.POST.get('movement_count', 0))
        except:
            movement_count = 0

        # ❌ ERRORS
        errors = 0

        total_questions = len(questions)

        for i, q in enumerate(questions):

            user_ans = request.POST.get(f"q{i+1}")

            if user_ans is None or user_ans != q["answer"]:
                errors += 1

        # 🎯 ACCURACY
        accuracy = (
            (total_questions - errors)
            / total_questions
        ) * 100

        # =====================================
        # 🔥 REALISTIC BEHAVIOR METRICS
        # =====================================

        # ⏱ Convert to minutes
        time_minutes = max(time_taken / 60, 0.1)

        # 🖱 Movement Rate per minute
        movement_rate = round(
            movement_count / time_minutes,
            2
        )

        # 😴 Idle Percentage
        idle_rate = round(
            (idle_time / time_taken) * 100,
            2
        )

        # =====================================
        # 🧠 LOAD DETECTION
        # =====================================

        load = calculate_cognitive_load(
            user_type,
            accuracy,
            time_taken,
            errors,
            movement_rate,
            idle_rate
        )

        # =====================================
        # 💾 SAVE DATABASE
        # =====================================

        TestResult.objects.create(

            user=request.user,

            user_type=user_type,

            time_taken=time_taken,

            errors=errors,

            load_level=load,

            cursor_movements=movement_count,

            idle_time=idle_time,

            movement_rate=movement_rate,

            idle_rate=idle_rate
        )

        # =====================================
        # 🧠 REALISTIC ANALYSIS
        # =====================================

        analysis = ""

        if user_type == "adhd":

            if movement_rate > 150:

                analysis += (
                    "High interaction frequency detected. "
                    "This may indicate hyperactivity or attention fluctuation. "
                )

            if idle_rate < 10:

                analysis += (
                    "Very low idle behavior suggests continuous rapid interaction. "
                )

        elif user_type == "dyslexia":

            if idle_rate > 25:

                analysis += (
                    "Extended pauses detected during question solving. "
                    "This may indicate reading or processing difficulty. "
                )

            if time_taken > 60:

                analysis += (
                    "Longer response duration suggests increased cognitive effort during reading tasks. "
                )

        else:

            analysis += (
                "Behavioral interaction patterns appear balanced and cognitively stable. "
            )

        # =====================================
        # 🎯 RESULT PAGE
        # =====================================

        return render(request, 'result.html', {

            'load': load,

            'errors': errors,

            'time': time_taken,

            'accuracy': round(accuracy, 2),

            'user_type': user_type,

            'movement_rate': movement_rate,

            'idle_rate': idle_rate,

            'analysis': analysis
        })

    return render(request, 'test.html', {

        'questions': questions,

        'start_time': time.time()

    })


# 🧠 LOAD CALCULATION LOGIC
def calculate_cognitive_load(

    user_type,
    accuracy,
    time_taken,
    errors,
    movement_rate,
    idle_rate

):

    # 🔥 ADHD
    if user_type == "adhd":

        if movement_rate > 180 or errors > 3:
            return "High"

        elif movement_rate > 120 or errors >= 2:
            return "Medium"

        else:
            return "Low"

    # 🔥 DYSLEXIA
    elif user_type == "dyslexia":

        if idle_rate > 30 or time_taken > 90:
            return "High"

        elif idle_rate > 20 or time_taken > 60:
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


# 📊 DASHBOARD
@login_required
def dashboard(request):

    results = TestResult.objects.filter(
        user=request.user
    ).order_by('-created_at')

    attempts = list(range(1, len(results) + 1))

    errors = [r.errors for r in results]

    times = [r.time_taken for r in results]

    movement_rates = [r.movement_rate for r in results]

    idle_rates = [r.idle_rate for r in results]

    total_questions = len(questions)

    accuracies = [

        round(
            ((total_questions - r.errors)
             / total_questions) * 100,
            2
        )

        for r in results
    ]

    # =====================================
    # 🧠 PERFORMANCE ANALYSIS
    # =====================================

    analysis = ""

    if len(results) == 0:

        analysis = "No test attempts available yet."

    else:

        avg_accuracy = sum(accuracies) / len(accuracies)

        avg_movement = sum(movement_rates) / len(movement_rates)

        avg_idle = sum(idle_rates) / len(idle_rates)

        if avg_accuracy >= 80:

            analysis += (
                "Recent performance appears accurate and stable. "
            )

        elif avg_accuracy >= 60:

            analysis += (
                "Moderate performance trend detected with scope for improvement. "
            )

        else:

            analysis += (
                "Recent attempts indicate increased cognitive strain. "
            )

        if avg_movement > 150:

            analysis += (
                "Higher movement frequency may indicate attention instability or restlessness. "
            )

        if avg_idle > 25:

            analysis += (
                "Extended pause behavior suggests increased cognitive processing effort. "
            )

    return render(request, 'dashboard.html', {

        'results': results,

        'attempts': attempts,

        'errors': errors,

        'times': times,

        'accuracies': accuracies,

        'movement_rates': movement_rates,

        'idle_rates': idle_rates,

        'analysis': analysis
    })