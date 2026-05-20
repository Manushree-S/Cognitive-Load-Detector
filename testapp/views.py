
from django.shortcuts import render, redirect
from .models import TestResult
import time
from django.contrib.auth.decorators import login_required


# =====================================================
# MULTI SUBJECT QUESTION BANK
# =====================================================

questions = {

    # =================================================
    # MATHEMATICS
    # =================================================

    "Mathematics": [

        {
            "q": "2 + 2 = ?",
            "options": ["3", "4", "5"],
            "answer": "4"
        },

        {
            "q": "5 × 3 = ?",
            "options": ["15", "10", "20"],
            "answer": "15"
        },

        {
            "q": "12 ÷ 4 = ?",
            "options": ["2", "3", "4"],
            "answer": "3"
        },
    ],

    # =================================================
    # SCIENCE
    # =================================================

    "Science": [

        {
            "q": "Water freezes at?",
            "options": ["0°C", "50°C", "100°C"],
            "answer": "0°C"
        },

        {
            "q": "The Earth revolves around?",
            "options": ["Moon", "Mars", "Sun"],
            "answer": "Sun"
        },

        {
            "q": "Humans breathe?",
            "options": ["Nitrogen", "Oxygen", "Hydrogen"],
            "answer": "Oxygen"
        },
    ],

    # =================================================
    # ENGLISH
    # =================================================

    "English": [

        {
            "passage": (
                "Riya loved reading books every evening after school. "
                "One day, she visited the library and discovered "
                "a science fiction novel about space exploration."
            ),

            "q": "Where did Riya discover the science fiction novel?",

            "options": [
                "Library",
                "Classroom",
                "Bookstore"
            ],

            "answer": "Library"
        },

        {
            "q": "Choose the correct spelling.",

            "options": [
                "Recieve",
                "Receive",
                "Receeve"
            ],

            "answer": "Receive"
        },

        {
            "q": "Opposite of 'Happy'?",

            "options": [
                "Sad",
                "Tall",
                "Fast"
            ],

            "answer": "Sad"
        },
    ],

    # =================================================
    # LOGICAL REASONING
    # =================================================

    "Logical Reasoning": [

        {
            "q": "Find the next number: 2, 4, 6, 8, ?",

            "options": [
                "9",
                "10",
                "12"
            ],

            "answer": "10"
        },

        {
            "q": "Which shape has 3 sides?",

            "options": [
                "Square",
                "Triangle",
                "Circle"
            ],

            "answer": "Triangle"
        },

        {
            "q": "Odd one out?",

            "options": [
                "Apple",
                "Banana",
                "Carrot"
            ],

            "answer": "Carrot"
        },
    ]
}


# =====================================================
# USER TYPE PAGE
# =====================================================

@login_required
def select_user_type(request):

    if request.method == "POST":

        user_type = request.POST.get(
            'user_type',
            'normal'
        )

        if user_type not in [
            'normal',
            'adhd',
            'dyslexia'
        ]:
            user_type = 'normal'

        request.session['user_type'] = user_type

        return redirect('/quiz/test/')

    return render(
        request,
        'user_type.html'
    )


# =====================================================
# COGNITIVE LOAD LOGIC
# =====================================================

def calculate_cognitive_load(

    user_type,
    accuracy,
    time_taken,
    errors,
    movement_rate,
    idle_rate

):

    if user_type == "adhd":

        if movement_rate > 180 or errors > 3:
            return "High"

        elif movement_rate > 120 or errors >= 2:
            return "Medium"

        else:
            return "Low"

    elif user_type == "dyslexia":

        if idle_rate > 30 or time_taken > 90:
            return "High"

        elif idle_rate > 20 or time_taken > 60:
            return "Medium"

        else:
            return "Low"

    else:

        if accuracy < 50 or time_taken > 60:
            return "High"

        elif accuracy < 80 or time_taken > 40:
            return "Medium"

        else:
            return "Low"


# =====================================================
# TEST PAGE
# =====================================================

@login_required
def test_page(request):

    user_type = request.session.get(
        'user_type',
        'normal'
    )

    if request.method == "POST":

        start_time = float(
            request.POST.get(
                'start_time',
                time.time()
            )
        )

        end_time = time.time()

        time_taken = round(
            end_time - start_time,
            2
        )

        try:
            idle_time = float(
                request.POST.get(
                    'idle_time',
                    0
                )
            )

        except:
            idle_time = 0

        try:
            movement_count = int(
                request.POST.get(
                    'movement_count',
                    0
                )
            )

        except:
            movement_count = 0

        # ==========================================
        # ANSWER CHECKING
        # ==========================================

        errors = 0

        total_questions = sum(
            len(qs) for qs in questions.values()
        )

        for subject, qs in questions.items():

            for i, q in enumerate(qs):

                user_ans = request.POST.get(
                    f"{subject}_{i}"
                )

                if (
                    user_ans is None
                    or user_ans != q["answer"]
                ):
                    errors += 1

        # ==========================================
        # ACCURACY
        # ==========================================

        accuracy = round(

            (
                (total_questions - errors)
                / total_questions
            ) * 100,

            2
        )

        # ==========================================
        # MOVEMENT RATE
        # ==========================================

        time_minutes = max(
            time_taken / 60,
            0.1
        )

        movement_rate = round(
            movement_count / time_minutes,
            2
        )

        # ==========================================
        # IDLE RATE
        # ==========================================

        idle_rate = round(

            (
                idle_time / time_taken
            ) * 100,

            2
        )

        # ==========================================
        # LOAD DETECTION
        # ==========================================

        load = calculate_cognitive_load(

            user_type,
            accuracy,
            time_taken,
            errors,
            movement_rate,
            idle_rate
        )

        # ==========================================
        # ANALYSIS
        # ==========================================

        analysis = ""

        if user_type == "adhd":

            if movement_rate > 150:

                analysis += (
                    "High interaction frequency detected. "
                    "Possible attention fluctuation observed. "
                )

            if idle_rate < 10:

                analysis += (
                    "Very low idle behavior suggests "
                    "continuous rapid interaction patterns. "
                )

        elif user_type == "dyslexia":

            if idle_rate > 25:

                analysis += (
                    "Extended pauses detected during "
                    "question solving and reading tasks. "
                )

            if time_taken > 60:

                analysis += (
                    "Longer response duration suggests "
                    "increased cognitive effort. "
                )

        else:

            analysis += (
                "Behavioral interaction patterns appear "
                "balanced and stable overall. "
            )

        # ==========================================
        # SAVE DATABASE
        # ==========================================

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

        # ==========================================
        # RESULT PAGE
        # ==========================================

        return render(

            request,

            'result.html',

            {

                'load': load,

                'errors': errors,

                'time': time_taken,

                'accuracy': accuracy,

                'user_type': user_type,

                'movement_rate': movement_rate,

                'idle_rate': idle_rate,

                'analysis': analysis
            }
        )

    return render(

        request,

        'test.html',

        {

            'questions': questions,

            'start_time': time.time()
        }
    )


# =====================================================
# DASHBOARD
# =====================================================

@login_required
def dashboard(request):

    results = TestResult.objects.filter(
        user=request.user
    ).order_by('-created_at')

    attempts = list(
        range(1, len(results) + 1)
    )

    errors = [
        r.errors for r in results
    ]

    times = [
        r.time_taken for r in results
    ]

    movement_rates = [
        r.movement_rate for r in results
    ]

    idle_rates = [
        r.idle_rate for r in results
    ]

    total_questions = sum(
        len(qs) for qs in questions.values()
    )

    accuracies = [

        round(

            (
                (total_questions - r.errors)
                / total_questions
            ) * 100,

            2

        )

        for r in results
    ]

    analysis = ""

    if len(results) == 0:

        analysis = (
            "No test attempts available yet."
        )

    else:

        avg_accuracy = (
            sum(accuracies)
            / len(accuracies)
        )

        avg_movement = (
            sum(movement_rates)
            / len(movement_rates)
        )

        avg_idle = (
            sum(idle_rates)
            / len(idle_rates)
        )

        if avg_accuracy >= 80:

            analysis += (
                "Recent performance appears accurate "
                "and cognitively stable. "
            )

        elif avg_accuracy >= 60:

            analysis += (
                "Moderate performance trend detected "
                "with room for improvement. "
            )

        else:

            analysis += (
                "Recent attempts indicate increased "
                "cognitive strain. "
            )

        if avg_movement > 150:

            analysis += (
                "Higher movement frequency may indicate "
                "attention instability or restlessness. "
            )

        if avg_idle > 25:

            analysis += (
                "Extended pause behavior suggests "
                "increased cognitive processing effort."
            )

    return render(

        request,

        'dashboard.html',

        {

            'results': results,

            'attempts': attempts,

            'errors': errors,

            'times': times,

            'accuracies': accuracies,

            'movement_rates': movement_rates,

            'idle_rates': idle_rates,

            'analysis': analysis
        }
    )

