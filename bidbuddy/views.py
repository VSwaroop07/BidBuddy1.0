from django.shortcuts import render, redirect
from .models import UserRegistration
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.contrib import messages
from .forms import ContactForm
from django.conf import settings
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse

import os
import json
import uuid
import threading
import gc
import sys
import platform
import traceback
import re
import csv
from functools import lru_cache

from .tender_config import UPLOAD_FOLDER, SUMMARY_FOLDER
from .tender_worker import process_pdf
from .tender_files import load_result

def home(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message = form.cleaned_data["message"]
            
            with open("responses.csv", "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([name, email, message])
            
            messages.success(request, "Message sent successfully!")
            return redirect("home")
    else:
        form = ContactForm()
    
    return render(request, "home.html", {"form": form})

def register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        industry = request.POST.get("industry")
        password = request.POST.get("password")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )

        UserRegistration.objects.create(
            name=name,
            email=email,
            industry=industry,
            password=password
        )

        return redirect('success')
    return render(request, 'register.html')

def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {
                'error': 'Invalid Email or Password'
            })
    return render(request, 'login.html')

def success(request):
    return render(request, 'successful.html')

@login_required
def profile(request):
    return render(request, "profile.html")

def logout_view(request):
    logout(request)
    return redirect('home')

def bidbuddy_trial(request):
    return render(request, "bidbuddy2.html")

def pro_version(request):
    return render(request, "pro_version.html")

def pay(request):
    if request.method == "POST":
        return redirect("payment_success")
    return render(request, "payment.html")

def payment_success(request):
    return render(request, "payment_success.html")

def free_trail(request):
    return render(request, "bidbuddy2.html")


def upload_file(request):
    """
    Accepts a PDF upload, saves it, kicks off OCR -> Gemini analysis
    in a background thread, and returns a job_id the frontend polls
    via check_summary(). Pipeline logic lives in tender_ocr.py /
    tender_ai.py / tender_worker.py (ported from the bidbuddy2 app).
    """
    if request.method != "POST" or not request.FILES.get("document"):
        return JsonResponse({"error": "No file uploaded"}, status=400)

    uploaded_file = request.FILES["document"]

    if not uploaded_file.name.lower().endswith(".pdf"):
        return JsonResponse({"error": "Only PDF files are supported."}, status=400)

    job_id = str(uuid.uuid4())

    pdf_path = os.path.join(UPLOAD_FOLDER, job_id + ".pdf")
    with open(pdf_path, "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    worker_thread = threading.Thread(
        target=process_pdf,
        args=(job_id, pdf_path),
        daemon=True,
    )
    worker_thread.start()

    return JsonResponse({
        "status": "processing",
        "job_id": job_id,
    })


def check_summary(request, job_id):
    result = load_result(job_id)

    if result is None:
        return JsonResponse({
            "ready": False,
            "summary": "Processing tender document with Gemini AI...",
        })

    return JsonResponse({
        "ready": True,
        "summary": result.get("summary", ""),
        "classification": result.get("classification", ""),
        "compliance": result.get("compliance", ""),
    })