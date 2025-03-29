import os
import uuid
from django.conf import settings
from .models import UserResource, ResourceRequest
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.units import inch
from django.template.loader import render_to_string
from django.utils.timezone import make_aware, now
from datetime import datetime
from django.contrib.auth.decorators import login_required
from lipa.models import Transaction


def home(request):
    return render(request, 'resources/home.html', {'title': 'Education'})

@login_required
def resources_history(request):
    user_resources = UserResource.objects.filter(user=request.user).order_by('-created')
    
    downloads = [{
        'filename': resource.filename,
        'created': resource.created,
        'display_name': resource.display_name
    } for resource in user_resources]
    
    context = {
        'title': 'My Resources',
        'downloads': downloads
    }
    return render(request, 'resources/history.html', context)

def schemes_of_work(request):
    return render(request, 'resources/schemes_of_work.html')

@login_required
@require_POST
def generate_schemes(request):
    teacher_name = request.POST.get('teacher_name', '').strip()
    tsc_number = request.POST.get('tsc_number', '').strip()
    school = request.POST.get('school', '').strip()
    level_type = request.POST.get('level_type', '').strip()
    level_number = request.POST.get('level_number', '').strip()
    subject = request.POST.get('subject', '').strip()
    term = request.POST.get('term', '').strip()
    year = request.POST.get('year', '').strip()

    if not all([teacher_name, school, level_type, level_number, subject, term, year]):
        error_msg = "Please fill in all required fields"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': error_msg}, status=400)
        return render(request, 'resources/schemes_of_work.html', {'error_msg': error_msg})

    token = uuid.uuid4()
    ResourceRequest.objects.create(
        user=request.user,
        parameters={
            'teacher_name': teacher_name,
            'tsc_number': tsc_number,
            'school': school,
            'level_type': level_type,
            'level_number': level_number,
            'subject': subject,
            'term': term,
            'year': year
        },
        token=token
    )
    
    success_url = request.build_absolute_uri(
        reverse('generate-schemes-success') + f"?token={token}"
    )
    payment_url = reverse('lipa-payment') + f"?amount=30&success_url={success_url}"
    return redirect(payment_url)

@login_required
def generate_schemes_success(request):
    token = request.GET.get('token')
    try:
        resource_request = ResourceRequest.objects.get(
            token=token,
            user=request.user,
            is_fulfilled=False
        )
        
        transaction = Transaction.objects.filter(
            user=request.user,
            success_url__contains=str(token),
            status='success'
        ).first()
        
        if not transaction:
            messages.error(request, "Payment not verified")
            return redirect('schemes-of-work')
        
        params = resource_request.parameters
        
        # PDF Generation Code
        subject = params['subject'].replace(" ", "_").lower()
        file_name = f"{params['level_type']}_{params['level_number']}_{subject}_term{params['term']}.pdf"
        existing_pdf_path = os.path.join(settings.SCHEMES_DIR, file_name)

        if not os.path.exists(existing_pdf_path):
            error_msg = f"Scheme not found for {params['level_type'].capitalize()} {params['level_number']} {params['subject'].replace('_', ' ').title()} Term {params['term']}"
            messages.error(request, error_msg)
            return redirect('schemes-of-work')

        temp_pdf_path = os.path.join(settings.MEDIA_ROOT, 'temp_first_page.pdf')
        c = canvas.Canvas(temp_pdf_path, pagesize=landscape(letter))

        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 550, f"SCHEMES OF WORK")
        c.setFont("Helvetica", 12)
        c.drawString(100, 525, f"For {params['level_type'].capitalize()} {params['level_number']} {params['subject'].replace('_', ' ').title()} - {params['year']} Term {params['term']}")
        c.drawString(100, 500, f"{params['teacher_name']}")
        if params['tsc_number']:
            c.drawString(100, 480, f"TSC Number: {params['tsc_number']}")
        c.drawString(100, 460, f"School: {params['school']}")

        footer_text = f"Generated on {now().strftime('%Y-%m-%d %H:%M')} by {params['teacher_name']}"
        c.setFont("Helvetica", 10)
        c.drawString(100, 50, footer_text)
        c.save()

        timestamp = now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"final_scheme_{params['teacher_name']}_{params['level_type']}{params['level_number']}_{subject}_term{params['term']}_{timestamp}.pdf"
        output_pdf_path = os.path.join(settings.MEDIA_ROOT, output_filename)
        
        pdf_writer = PdfWriter()
        first_page = PdfReader(temp_pdf_path).pages[0]
        pdf_writer.add_page(first_page)

        existing_pdf = PdfReader(existing_pdf_path)
        for page in existing_pdf.pages:
            temp_page_path = os.path.join(settings.MEDIA_ROOT, 'temp_page.pdf')
            header_footer_canvas = canvas.Canvas(temp_page_path, pagesize=landscape(letter))
            header_footer_canvas.setFont("Helvetica", 9)
            header_text = f"{params['teacher_name']} | {params['school']} | {params['level_type'].capitalize()} {params['level_number']} {params['subject'].replace('_', ' ').title()} | Term {params['term']} {params['year']}"
            header_footer_canvas.drawString(50, 580, header_text)
            footer_text = f"Page {len(pdf_writer.pages)} | Generated on {now().strftime('%Y-%m-%d')} by {params['teacher_name']}"
            if params['tsc_number']:
                footer_text += f" (TSC: {params['tsc_number']})"
            header_footer_canvas.drawString(50, 20, footer_text)
            header_footer_canvas.save()
            header_footer_page = PdfReader(temp_page_path).pages[0]
            page.merge_page(header_footer_page)
            pdf_writer.add_page(page)

        with open(output_pdf_path, 'wb') as out:
            pdf_writer.write(out)

        for temp_file in [temp_pdf_path, os.path.join(settings.MEDIA_ROOT, 'temp_page.pdf')]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        display_name = (
            f"{params['level_type'].capitalize()} {params['level_number']} {params['subject'].replace('_', ' ').title()} "
            f"Term {params['term']} ({now().strftime('%Y-%m-%d')})"
        )
        
        UserResource.objects.create(
            user=request.user,
            filename=output_filename,
            display_name=display_name,
            created=now()
        )

        resource_request.is_fulfilled = True
        resource_request.save()
        
        return redirect('resources-history')
        
    except ResourceRequest.DoesNotExist:
        messages.error(request, "Invalid or expired request")
        return redirect('schemes-of-work')

@login_required
def download_resource(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    
    if not filename.startswith('final_scheme_') or not filename.endswith('.pdf'):
        raise Http404("Invalid file requested")
    
    if not UserResource.objects.filter(user=request.user, filename=filename).exists():
        raise Http404("File not found or access denied")
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    raise Http404("File not found")

@login_required
@require_POST
def delete_resource(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    
    if not filename.startswith('final_scheme_') or not filename.endswith('.pdf'):
        messages.error(request, "Invalid file requested")
        return redirect('resources-history')
    
    try:
        resource = UserResource.objects.filter(user=request.user, filename=filename).first()
        if not resource:
            messages.error(request, "File not found or access denied")
            return redirect('resources-history')
        
        if os.path.exists(file_path):
            os.remove(file_path)
            resource.delete()
            messages.success(request, "Resource deleted successfully")
        else:
            messages.error(request, "File not found")
    except Exception as e:
        messages.error(request, f"Error deleting file: {str(e)}")
    
    return redirect('resources-history')