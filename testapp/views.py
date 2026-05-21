from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import TestResult

import time


QUESTION_BANK = {
    "1-2": {
        "Mathematics": [
            {"q": "2 + 2 = ?", "options": ["3", "4", "5"], "answer": "4"},
            {"q": "5 - 2 = ?", "options": ["2", "3", "4"], "answer": "3"},
        ],
        "English": [
            {"q": "Opposite of hot?", "options": ["Cold", "Big", "Fast"], "answer": "Cold"},
            {"q": "Choose the correct spelling.", "options": ["Apple", "Aple", "Appl"], "answer": "Apple"},
        ],
    },
    "3-5": {
        "Mathematics": [
            {"q": "12 / 4 = ?", "options": ["2", "3", "4"], "answer": "3"},
            {"q": "15 + 10 = ?", "options": ["20", "25", "30"], "answer": "25"},
        ],
        "Science": [
            {"q": "Humans breathe which gas?", "options": ["Oxygen", "Hydrogen", "Nitrogen"], "answer": "Oxygen"},
            {"q": "The Sun is a...", "options": ["Planet", "Star", "Moon"], "answer": "Star"},
        ],
    },
    "6-8": {
        "Mathematics": [
            {"q": "25 x 4 = ?", "options": ["100", "75", "125"], "answer": "100"},
            {"q": "Square root of 81?", "options": ["8", "9", "7"], "answer": "9"},
        ],
        "Reasoning": [
            {"q": "Find the next number: 2, 4, 6, 8, ?", "options": ["10", "12", "9"], "answer": "10"},
            {"q": "Which word does not belong?", "options": ["Circle", "Square", "Blue"], "answer": "Blue"},
        ],
    },
    "9-10": {
        "Mathematics": [
            {"q": "Solve: 3x = 27", "options": ["6", "9", "12"], "answer": "9"},
            {"q": "Approximate value of pi?", "options": ["3.14", "2.14", "4.13"], "answer": "3.14"},
        ],
        "Science": [
            {"q": "Formula of water?", "options": ["CO2", "H2O", "NaCl"], "answer": "H2O"},
            {"q": "Which organ pumps blood?", "options": ["Heart", "Lung", "Kidney"], "answer": "Heart"},
        ],
    },
}


def landing_page(request):
    return render(request, "landing.html")


@login_required
def student_details(request):
    if request.method == "POST":
        student_name = request.POST.get("student_name", "").strip()
        grade_level = request.POST.get("grade_level", "3-5")

        if not student_name:
            return render(
                request,
                "student_form.html",
                {
                    "error": "Please enter the student's name.",
                    "grade_level": grade_level,
                },
            )

        request.session["student_name"] = student_name
        request.session["grade_level"] = grade_level
        request.session.pop("latest_result", None)

        return redirect("test")

    return render(request, "student_form.html")


@login_required
def test_page(request):
    student_name = request.session.get("student_name")
    grade_level = request.session.get("grade_level")

    if not student_name or not grade_level:
        return redirect("student_details")

    questions = QUESTION_BANK.get(grade_level, QUESTION_BANK["3-5"])

    if request.method == "POST":
        start_time = float(request.POST.get("start_time", time.time()))
        time_taken = round(time.time() - start_time, 2)
        random_movements = int(
            request.POST.get("random_movement_count")
            or request.POST.get("movement_count", 0)
        )
        option_switches = int(request.POST.get("option_switch_count", 0))
        movement_count = random_movements + option_switches
        idle_time = int(request.POST.get("idle_time", 0))
        focus_events = int(request.POST.get("focus_events", 0))
        face_missing_events = int(request.POST.get("face_missing_events", 0))
        reading_support_events = int(request.POST.get("reading_support_events", 0))
        support_signal = request.POST.get("support_signal", "comfortable")

        total_questions = 0
        correct_answers = 0
        subject_scores = {}

        for subject, qs in questions.items():
            subject_correct = 0

            for i, question in enumerate(qs):
                total_questions += 1
                answer = request.POST.get(f"{subject}_{i}")

                if answer == question["answer"]:
                    correct_answers += 1
                    subject_correct += 1

            subject_scores[subject] = round((subject_correct / len(qs)) * 100, 2)

        errors = total_questions - correct_answers
        accuracy = round((correct_answers / max(total_questions, 1)) * 100, 2)
        movement_rate = round(movement_count / max(time_taken, 1), 2)
        random_movement_rate = round(random_movements / max(time_taken, 1), 2)
        option_switch_rate = round(option_switches / max(total_questions, 1), 2)
        idle_rate = round((idle_time / max(time_taken, 1)) * 100, 2)
        attention_score = max(
            0,
            min(
                100,
                round(
                    accuracy
                    - min(random_movement_rate * 1.5, 15)
                    - min(option_switch_rate * 8, 20)
                    - min(idle_rate * 0.25, 20)
                    - min(focus_events * 4, 20)
                    - min(face_missing_events * 2, 10)
                    - min(reading_support_events * 5, 15),
                    2,
                ),
            ),
        )

        if attention_score >= 80:
            load = "Low"
        elif attention_score >= 50:
            load = "Medium"
        else:
            load = "High"

        feedback = get_grade_feedback(grade_level, load, accuracy)
        graph_analysis = get_graph_analysis(
            grade_level,
            load,
            accuracy,
            attention_score,
            random_movement_rate,
            option_switch_rate,
            idle_rate,
            face_missing_events,
            support_signal,
        )
        camera_analysis = get_camera_analysis(
            face_missing_events,
            reading_support_events,
            support_signal,
        )
        analysis = (
            f"{student_name} scored {accuracy}% with an attention score of "
            f"{attention_score}. The system observed {random_movement_rate} "
            f"random cursor moves/sec, {option_switch_rate} option switches per "
            f"question, {idle_rate}% idle time, and {focus_events} window "
            f"switches. Camera support recorded {face_missing_events} face "
            f"visibility interruptions and {reading_support_events} student "
            f"support signals. This pattern indicates "
            f"{load.lower()} cognitive load for the selected grade band."
        )

        TestResult.objects.create(
            user=request.user,
            user_type="normal",
            subject=grade_level,
            load_level=load,
            accuracy=accuracy,
            attention_score=attention_score,
            errors=errors,
            time_taken=time_taken,
            cursor_movements=movement_count,
            random_movements=random_movements,
            option_switches=option_switches,
            idle_time=idle_time,
            movement_rate=movement_rate,
            random_movement_rate=random_movement_rate,
            option_switch_rate=option_switch_rate,
            idle_rate=idle_rate,
        )

        request.session["latest_result"] = {
            "student_name": student_name,
            "grade_level": grade_level,
            "accuracy": accuracy,
            "attention_score": attention_score,
            "load": load,
            "time_taken": time_taken,
            "movement_count": movement_count,
            "random_movements": random_movements,
            "option_switches": option_switches,
            "movement_rate": movement_rate,
            "random_movement_rate": random_movement_rate,
            "option_switch_rate": option_switch_rate,
            "idle_rate": idle_rate,
            "focus_events": focus_events,
            "face_missing_events": face_missing_events,
            "reading_support_events": reading_support_events,
            "support_signal": support_signal,
            "subject_scores": subject_scores,
            "feedback": feedback,
            "analysis": analysis,
            "graph_analysis": graph_analysis,
            "camera_analysis": camera_analysis,
        }

        return redirect("result")

    return render(
        request,
        "test.html",
        {
            "student_name": student_name,
            "grade_level": grade_level,
            "questions": questions,
            "start_time": time.time(),
        },
    )


@login_required
def result_page(request):
    result = request.session.get("latest_result")

    if not result:
        return redirect("student_details")

    return render(request, "result.html", result)


@login_required
def dashboard(request):
    results = TestResult.objects.filter(user=request.user).order_by("-created_at")
    chart_results = list(results.order_by("created_at"))
    attempts = list(range(1, len(chart_results) + 1))
    errors = [result.errors for result in chart_results]

    if chart_results:
        latest = chart_results[-1]
        analysis = (
            f"Latest assessment shows {latest.load_level.lower()} cognitive load "
            f"with {latest.accuracy}% accuracy and an attention score of "
            f"{latest.attention_score}."
        )
    else:
        analysis = "No assessment attempts are available yet."

    return render(
        request,
        "dashboard.html",
        {
            "results": results,
            "attempts": attempts,
            "errors": errors,
            "analysis": analysis,
        },
    )


def get_grade_feedback(grade_level, load, accuracy):
    feedback = {
        "1-2": {
            "Low": "Great job. You listened, tried, and chose your answers well.",
            "Medium": "Good try. Next time, go slowly and pick one answer after reading.",
            "High": "Nice effort. Take a short break, hear the question, and try again.",
        },
        "3-5": {
            "Low": "Good work. You stayed focused and understood the questions well.",
            "Medium": "Nice effort. Read the question once more before choosing your answer.",
            "High": "Keep trying. Use read-aloud, examples, and shorter practice rounds.",
        },
        "6-8": {
            "Low": "Good control and steady thinking. You can try slightly harder mixed questions.",
            "Medium": "You are close. Break each question into steps before changing answers.",
            "High": "Slow the task down. Use examples first, then answer one step at a time.",
        },
        "9-10": {
            "Low": "Your accuracy and attention look steady. You can increase difficulty gradually while keeping the same calm pace.",
            "Medium": "Good foundation. Review the concept behind missed questions and avoid rushing between similar options.",
            "High": "Focus on strategy first. Revise the core topic, solve one worked example, then attempt timed questions later.",
        },
    }

    message = feedback.get(grade_level, feedback["3-5"]).get(load, feedback["3-5"]["Medium"])

    if accuracy >= 80:
        return f"{message} Your score shows strong understanding."
    if accuracy >= 50:
        return f"{message} You have a good start to build on."
    return f"{message} This attempt helps us choose the right support."


def get_graph_analysis(
    grade_level,
    load,
    accuracy,
    attention_score,
    random_movement_rate,
    option_switch_rate,
    idle_rate,
    face_missing_events,
    support_signal,
):
    grade_text = {
        "1-2": {
            "Low": "The graph shows many good answers and calm work.",
            "Medium": "The graph shows you tried well. Going slower can help.",
            "High": "The graph shows the test may have felt hard. Small steps can help.",
        },
        "3-5": {
            "Low": "The graph shows good answers and steady attention.",
            "Medium": "The graph shows you are learning. Fewer answer changes may help.",
            "High": "The graph shows you may need easier steps and more examples first.",
        },
        "6-8": {
            "Low": "The graph shows steady attention and good control across the assessment.",
            "Medium": "The graph suggests the student understood parts of the test but may have switched answers while deciding.",
            "High": "The graph points to cognitive overload. Reduce task density and help the student plan before answering.",
        },
        "9-10": {
            "Low": "The graph shows stable analytical performance and readiness for slightly harder practice.",
            "Medium": "The graph suggests concept review and slower option comparison will improve accuracy.",
            "High": "The graph shows that accuracy, attention, and behavior signals need structured revision before timed work.",
        },
    }

    base = grade_text.get(grade_level, grade_text["3-5"]).get(load, grade_text["3-5"]["Medium"])
    strongest_signal = "accuracy"
    signal_value = accuracy

    if idle_rate > 25:
        strongest_signal = "idle time"
        signal_value = idle_rate
    elif option_switch_rate > 0.75:
        strongest_signal = "answer switching"
        signal_value = option_switch_rate
    elif random_movement_rate > 4:
        strongest_signal = "random movement"
        signal_value = random_movement_rate
    elif face_missing_events > 1:
        strongest_signal = "camera visibility"
        signal_value = face_missing_events
    elif support_signal != "comfortable":
        strongest_signal = "student support check"
        signal_value = support_signal.replace("_", " ")
    elif attention_score < 60:
        strongest_signal = "attention score"
        signal_value = attention_score

    grade_suffix = {
        "1-2": "Next step: try slowly, listen carefully, and celebrate each correct answer.",
        "3-5": "Next step: read, think, remove wrong choices, then answer.",
        "6-8": "Next step: plan the answer before switching options.",
        "9-10": "Next step: review the concept behind missed questions before timed practice.",
    }

    return (
        f"{base} Main area to watch: {strongest_signal} "
        f"({signal_value}). {grade_suffix.get(grade_level, grade_suffix['3-5'])}"
    )


def get_camera_analysis(face_missing_events, reading_support_events, support_signal):
    if support_signal == "reading_hard":
        return (
            "The student selected that reading felt hard. This is not a diagnosis, "
            "but it is a helpful cue to use voice reading, larger spacing, and a slower pace."
        )

    if support_signal == "need_break":
        return (
            "The student asked for a break. A short pause can help the learner return with better focus."
        )

    if face_missing_events > 2:
        return (
            "The camera could not see the learner clearly several times. This may mean they looked away, "
            "moved out of frame, or needed support staying with the task."
        )

    if reading_support_events > 0:
        return (
            "The student used the support check during the test. Keep the session calm and offer help early."
        )

    return (
        "Camera support did not record a strong concern. Continue using the camera as a gentle support cue, "
        "not as a medical stress detector."
    )
