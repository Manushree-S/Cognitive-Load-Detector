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

        feedback = get_answer_feedback(
            grade_level,
            correct_answers,
            errors,
            total_questions,
            load,
        )
        graph_analysis = get_graph_analysis(
            grade_level,
            correct_answers,
            errors,
            total_questions,
            load,
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
        analysis = get_result_analysis(
            grade_level,
            student_name,
            correct_answers,
            errors,
            total_questions,
            attention_score,
            random_movement_rate,
            option_switch_rate,
            idle_rate,
            focus_events,
            face_missing_events,
            reading_support_events,
            load,
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
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "incorrect_answers": errors,
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


def get_result_analysis(
    grade_level,
    student_name,
    correct_answers,
    incorrect_answers,
    total_questions,
    attention_score,
    random_movement_rate,
    option_switch_rate,
    idle_rate,
    focus_events,
    face_missing_events,
    reading_support_events,
    load,
):
    if grade_level in {"1-2", "3-5"}:
        return (
            f"{student_name} got {correct_answers} out of {total_questions} "
            f"answers right. {incorrect_answers} answer"
            f"{'' if incorrect_answers == 1 else 's'} can be practiced again. "
            f"The work looked {load.lower()} load, so the next practice can stay "
            "calm, short, and step by step."
        )

    if grade_level == "6-8":
        return (
            f"{student_name} answered {correct_answers} out of {total_questions} "
            f"questions correctly, with {incorrect_answers} to review. The attention "
            f"score was {attention_score}, and the attempt showed {load.lower()} "
            "cognitive load. The next practice should focus on checking answers "
            "before switching choices."
        )

    return (
        f"{student_name} answered {correct_answers} out of {total_questions} "
        f"questions correctly and had {incorrect_answers} answers to review. "
        f"The attention score was {attention_score}. The system observed "
        f"{random_movement_rate} random cursor moves/sec, {option_switch_rate} "
        f"option switches per question, {idle_rate}% idle time, and {focus_events} "
        f"window switches. Camera support recorded {face_missing_events} face "
        f"visibility interruptions and {reading_support_events} student support "
        f"signals. This pattern indicates {load.lower()} cognitive load for this attempt."
    )


def get_answer_feedback(grade_level, correct_answers, incorrect_answers, total_questions, load):
    if grade_level == "1-2":
        return get_early_primary_feedback(
            correct_answers,
            incorrect_answers,
            total_questions,
            load,
        )

    if grade_level == "3-5":
        return get_primary_feedback(
            correct_answers,
            incorrect_answers,
            total_questions,
            load,
        )

    if grade_level == "6-8":
        return get_middle_feedback(
            correct_answers,
            incorrect_answers,
            total_questions,
            load,
        )

    return get_high_feedback(correct_answers, incorrect_answers, total_questions, load)


def get_early_primary_feedback(correct_answers, incorrect_answers, total_questions, load):
    if correct_answers == total_questions:
        strength = f"Wonderful work. You got all {total_questions} answers right."
    elif correct_answers > 0:
        strength = f"Good trying. You got {correct_answers} answer{'' if correct_answers == 1 else 's'} right."
    else:
        strength = "Good trying. You finished the test, and that is a brave start."

    if incorrect_answers == 0:
        next_step = "Keep going slowly and carefully."
    elif incorrect_answers == 1:
        next_step = "Try the one tricky question again with help."
    else:
        next_step = f"Try the {incorrect_answers} tricky questions again, one by one."

    load_step = {
        "Low": "Your calm work helped you.",
        "Medium": "Take a small pause before you choose.",
        "High": "A short break and read-aloud can help next time.",
    }

    return f"{strength} {next_step} {load_step.get(load, load_step['Medium'])}"


def get_primary_feedback(correct_answers, incorrect_answers, total_questions, load):
    if correct_answers == total_questions:
        strength = f"Great job. You got all {total_questions} answers correct."
    elif correct_answers >= max(1, total_questions * 0.75):
        strength = f"Great effort. You got {correct_answers} out of {total_questions} correct."
    elif correct_answers >= max(1, total_questions * 0.5):
        strength = f"Good work. You got {correct_answers} out of {total_questions} correct."
    elif correct_answers > 0:
        strength = f"Nice try. You got {correct_answers} answer{'' if correct_answers == 1 else 's'} correct."
    else:
        strength = "Nice try. You completed the test, and now we know what to practice."

    if incorrect_answers == 0:
        next_step = "Keep using the same careful thinking."
    elif incorrect_answers == 1:
        next_step = "Practice the one question that was tricky."
    else:
        next_step = f"Practice the {incorrect_answers} tricky questions slowly, one at a time."

    load_step = {
        "Low": "You looked steady while working.",
        "Medium": "Next time, read the question twice before choosing.",
        "High": "Next time, try a shorter round or use read-aloud help.",
    }

    return f"{strength} {next_step} {load_step.get(load, load_step['Medium'])}"


def get_middle_feedback(correct_answers, incorrect_answers, total_questions, load):
    if correct_answers == total_questions:
        strength = (
            f"Excellent work. You answered all {total_questions} questions correctly, "
            "which shows careful reading and strong understanding."
        )
    elif correct_answers >= max(1, total_questions * 0.75):
        strength = (
            f"Great effort. You answered {correct_answers} out of {total_questions} "
            "questions correctly, so most choices were on track."
        )
    elif correct_answers >= max(1, total_questions * 0.5):
        strength = (
            f"Good start. You answered {correct_answers} out of {total_questions} "
            "questions correctly, giving you a clear base to build from."
        )
    elif correct_answers > 0:
        strength = (
            f"You completed the attempt and got {correct_answers} answer"
            f"{'' if correct_answers == 1 else 's'} correct, so there are ideas "
            "you already understand."
        )
    else:
        strength = "You completed the attempt, which helps us choose the right support."

    if incorrect_answers == 0:
        review = "Next step: keep the same calm strategy and try a small challenge."
    elif incorrect_answers == 1:
        review = "Next step: review the one answer that needs practice, then try a similar question."
    else:
        review = (
            f"Next step: review the {incorrect_answers} answers that need practice "
            "one at a time, and remove choices that clearly do not fit."
        )

    load_steps = {
        "Low": "Your work pattern looked steady, so keep using this pace.",
        "Medium": "To grow from here, pause before changing an answer.",
        "High": "Shorter practice rounds and examples can make the next attempt easier.",
    }

    return f"{strength} {review} {load_steps.get(load, load_steps['Medium'])}"


def get_high_feedback(correct_answers, incorrect_answers, total_questions, load):
    if correct_answers == total_questions:
        strength = (
            f"Excellent work. You answered all {total_questions} questions correctly, "
            "showing strong command of this set."
        )
    elif correct_answers >= max(1, total_questions * 0.75):
        strength = (
            f"Strong effort. You answered {correct_answers} out of {total_questions} "
            "questions correctly, so your core understanding is solid."
        )
    elif correct_answers >= max(1, total_questions * 0.5):
        strength = (
            f"Good foundation. You answered {correct_answers} out of {total_questions} "
            "questions correctly, and the remaining items show where to focus review."
        )
    elif correct_answers > 0:
        strength = (
            f"This attempt gives useful direction. You answered {correct_answers} "
            f"out of {total_questions} correctly, so start review from what already worked."
        )
    else:
        strength = "This attempt gives useful evidence about what to rebuild before the next round."

    if incorrect_answers == 0:
        review = "Next step: increase difficulty gradually while keeping the same strategy."
    elif incorrect_answers == 1:
        review = "Next step: review the one missed item and identify the concept behind it."
    else:
        review = (
            f"Next step: group the {incorrect_answers} review items by concept, "
            "then practice one concept before returning to timed work."
        )

    load_steps = {
        "Low": "The work pattern looked steady.",
        "Medium": "Before changing an answer, compare the two closest options carefully.",
        "High": "Use untimed practice first, then return to timed questions later.",
    }

    return f"{strength} {review} {load_steps.get(load, load_steps['Medium'])}"


def get_graph_analysis(
    grade_level,
    correct_answers,
    incorrect_answers,
    total_questions,
    load,
    attention_score,
    random_movement_rate,
    option_switch_rate,
    idle_rate,
    face_missing_events,
    support_signal,
):
    if grade_level in {"1-2", "3-5"}:
        base = (
            f"The graph shows {correct_answers} correct and "
            f"{incorrect_answers} to practice."
        )
    elif grade_level == "6-8":
        base = (
            f"The graph shows {correct_answers} correct and "
            f"{incorrect_answers} to review out of {total_questions} questions."
        )
    else:
        base = (
            f"The graph connects the answer pattern with behavior signals: "
            f"{correct_answers} correct and {incorrect_answers} to review out of "
            f"{total_questions} questions."
        )
    strongest_signal = "answers to review"
    signal_value = incorrect_answers

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

    if grade_level in {"1-2", "3-5"}:
        signal_names = {
            "answers to review": "questions to practice",
            "idle time": "pause time",
            "answer switching": "changing answers",
            "random movement": "extra mouse movement",
            "camera visibility": "sitting clearly",
            "student support check": "help request",
            "attention score": "focus",
        }
        next_step = {
            "Low": "Keep going at this pace.",
            "Medium": "Read slowly, then choose.",
            "High": "Try fewer questions with help first.",
        }
        strongest_signal = signal_names.get(strongest_signal, strongest_signal)
    elif grade_level == "6-8":
        next_step = {
            "Low": "Next step: keep the same pace and review any missed answer briefly.",
            "Medium": "Next step: slow down answer changes and check the question before choosing.",
            "High": "Next step: reduce the number of questions per round and practice with examples first.",
        }
    else:
        next_step = {
            "Low": "Next step: keep the same pace and review any missed answer briefly.",
            "Medium": "Next step: compare close options before changing an answer.",
            "High": "Next step: use untimed concept review before returning to timed practice.",
        }

    return (
        f"{base} Main area to watch: {strongest_signal} "
        f"({signal_value}). {next_step.get(load, next_step['Medium'])}"
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
