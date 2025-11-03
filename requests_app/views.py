from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.http import HttpResponse
from django.db.models import Count, Q
from .models import ServiceRequest
from .forms import ServiceRequestForm, UserRegistrationForm, ResolutionStepForm
from django.conf import settings
from django.contrib import messages
import requests  # used for simple SendGrid or mock API call
from datetime import datetime, timedelta

# Add these imports for user management
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

def home(request):
    """
    Home page view that redirects authenticated users appropriately:
    - Staff users: redirect to dashboard (full view)
    - Regular users: redirect to dashboard (personal view)
    - Anonymous users: show public home page
    """
    if request.user.is_authenticated:
        return redirect('requests_app:ui_dashboard')
    
    # Show public home page for non-authenticated users
    return render(request, 'home.html')

def ui_submit(request):
    return render(request, 'submit.html')

@login_required
def ui_dashboard(request):
    # Different data based on user role
    if request.user.is_staff:
        # ADMIN/STAFF DASHBOARD - Full statistics
        total_requests = ServiceRequest.objects.count()
        pending_count = ServiceRequest.objects.filter(status='Pending').count()
        in_progress_count = ServiceRequest.objects.filter(status='In Progress').count()
        resolved_count = ServiceRequest.objects.filter(status='Resolved').count()
        
        # Recent activity (last 7 days) - all requests
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_requests = ServiceRequest.objects.filter(created_at__gte=seven_days_ago).count()
        
        # Requests by category - all requests
        category_stats = ServiceRequest.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Monthly trend (last 6 months) - all requests
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_trend = ServiceRequest.objects.filter(
            created_at__gte=six_months_ago
        ).extra({
            'month': "strftime('%%Y-%%m', created_at)"
        }).values('month').annotate(count=Count('id')).order_by('month')
        
        # High priority requests (pending + in progress) - all requests
        high_priority_count = ServiceRequest.objects.filter(
            Q(status='Pending') | Q(status='In Progress')
        ).count()
        
        # Average resolution time (for resolved requests) - all requests
        avg_resolution_time = None
        # Note: You'll need to fix the resolved_at issue mentioned earlier
        
        dashboard_type = 'admin'
        
    else:
        # REGULAR USER DASHBOARD - Only user's own statistics
        user_name = request.user.get_full_name() or request.user.username
        
        # User's own requests
        user_requests = ServiceRequest.objects.filter(requester_name=user_name)
        total_requests = user_requests.count()
        pending_count = user_requests.filter(status='Pending').count()
        in_progress_count = user_requests.filter(status='In Progress').count()
        resolved_count = user_requests.filter(status='Resolved').count()
        
        # Recent activity (last 7 days) - user's requests only
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_requests = user_requests.filter(created_at__gte=seven_days_ago).count()
        
        # Requests by category - user's requests only
        category_stats = user_requests.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Monthly trend (last 6 months) - user's requests only
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_trend = user_requests.filter(
            created_at__gte=six_months_ago
        ).extra({
            'month': "strftime('%%Y-%%m', created_at)"
        }).values('month').annotate(count=Count('id')).order_by('month')
        
        # High priority requests (pending + in progress) - user's requests only
        high_priority_count = user_requests.filter(
            Q(status='Pending') | Q(status='In Progress')
        ).count()
        
        # Average resolution time for user's resolved requests
        resolved_user_requests = user_requests.filter(status='Resolved')
        avg_resolution_time = None
        # Note: You'll need to fix the resolved_at issue mentioned earlier
        
        dashboard_type = 'user'
    
    context = {
        'total_requests': total_requests,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
        'recent_requests': recent_requests,
        'category_stats': category_stats,
        'monthly_trend': list(monthly_trend),
        'high_priority_count': high_priority_count,
        'avg_resolution_time': avg_resolution_time,
        'dashboard_type': dashboard_type,  # This will help in template
        'user': request.user,
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def ui_requests_list(request):
    if not request.user.is_staff:
        return HttpResponse("Forbidden", status=403)
    return render(request, 'requests_list.html')

@login_required
def ui_request_detail(request):
    if not request.user.is_staff:
        return HttpResponse("Forbidden", status=403)
    return render(request, 'request_detail.html')

def ui_login(request):
    return render(request, 'login.html')


def signup(request):
    # Only staff can register users
    if not request.user.is_staff:
        return HttpResponse("Forbidden. Only administrators can register users.", status=403)
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Don't auto-login when admin creates user - redirect to success
            return redirect('requests_app:signup_success')
    else:
        form = UserRegistrationForm()
    return render(request, 'signup.html', {'form': form})

def signup_success(request):
    return render(request, 'signup_success.html')

@login_required
def submit_request(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST, user=request.user)
        if form.is_valid():
            req = form.save(commit=False)
            # Auto-populate requester_name from logged-in user
            req.requester_name = request.user.get_full_name() or request.user.username
            # Auto-populate department from user profile if not provided
            try:
                if not req.department and hasattr(request.user, 'profile') and request.user.profile.department:
                    req.department = request.user.profile.department
            except AttributeError:
                # User doesn't have a profile yet - that's okay, department remains empty
                pass
            req.save()  # default status = Pending
            # Send notification (simple example using SendGrid HTTP API)
            send_new_request_email(req)
            # Redirect to success page with message
            return redirect('requests_app:submit_success')
    else:
        form = ServiceRequestForm(user=request.user)
    return render(request, 'submit.html', {'form': form, 'user': request.user})

def submit_success(request):
    # Show success message on the submit page
    return render(request, 'submit.html', {'success': True, 'form': ServiceRequestForm(user=request.user if request.user.is_authenticated else None), 'user': request.user if request.user.is_authenticated else None})

# Admin view — require staff status
@login_required
def list_requests(request):
    if not request.user.is_staff:
        # Redirect non-staff to their own requests
        return redirect('requests_app:my_requests')
    qs = ServiceRequest.objects.order_by('-created_at')
    # simple filtering via GET params (optional)
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    return render(request, 'requests_list.html', {'requests': qs, 'user': request.user, 'is_my_requests': False})

@login_required
def detail_request(request, pk):
    req = get_object_or_404(ServiceRequest, pk=pk)
    
    # Non-staff users can only view their own requests
    if not request.user.is_staff:
        user_name = request.user.get_full_name() or request.user.username
        if req.requester_name != user_name:
            return HttpResponse("Forbidden", status=403)
    
    resolution_steps = req.resolution_steps.all()
    step_form = ResolutionStepForm()
    
    # Handle status updates and resolution steps for staff users
    if request.method == 'POST' and request.user.is_staff:
        # Handle status changes - ONLY when explicitly requested
        if 'mark_resolved' in request.POST:
            req.mark_resolved(user=request.user)
            messages.success(request, f'Request #{req.id} has been marked as resolved!')
        elif 'mark_in_progress' in request.POST:
            req.status = 'In Progress'
            req.save()
            messages.success(request, f'Request #{req.id} is now in progress!')
        elif 'mark_pending' in request.POST:
            req.status = 'Pending'
            req.save()
            messages.success(request, f'Request #{req.id} has been reopened!')
        
        # Handle adding resolution steps - NO automatic status change
        elif 'add_resolution_step' in request.POST:
            step_form = ResolutionStepForm(request.POST)
            if step_form.is_valid():
                resolution_step = step_form.save(commit=False)
                resolution_step.service_request = req
                resolution_step.created_by = request.user
                resolution_step.save()
                messages.success(request, 'Resolution step added successfully!')
                return redirect('requests_app:detail_request', pk=pk)
        
        # Handle deleting resolution steps - NO automatic status change
        elif 'delete_step' in request.POST:
            step_id = request.POST.get('step_id')
            try:
                step = ResolutionStep.objects.get(id=step_id, service_request=req)
                step.delete()
                messages.success(request, 'Resolution step deleted successfully!')
            except ResolutionStep.DoesNotExist:
                messages.error(request, 'Step not found.')
        
        return redirect('requests_app:detail_request', pk=pk)
    
    context = {
        'req': req,
        'user': request.user,
        'resolution_steps': resolution_steps,
        'step_form': step_form,
    }
    
    return render(request, 'request_detail.html', context)

@login_required
def my_requests(request):
    # Only show user's own requests (non-staff users)
    user_name = request.user.get_full_name() or request.user.get_username()
    qs = ServiceRequest.objects.filter(requester_name=user_name).order_by('-created_at')
    
    # Calculate counts for the template
    total_count = qs.count()
    pending_count = qs.filter(status='Pending').count()
    in_progress_count = qs.filter(status='In Progress').count()
    resolved_count = qs.filter(status='Resolved').count()
    
    return render(request, 'requests_list.html', {
        'requests': qs, 
        'user': request.user, 
        'is_my_requests': True,
        'total_count': total_count,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
    })

@login_required
def list_requests(request):
    if not request.user.is_staff:
        # Redirect non-staff to their own requests
        return redirect('requests_app:my_requests')
    qs = ServiceRequest.objects.order_by('-created_at')
    
    # Calculate counts for the template
    total_count = qs.count()
    pending_count = qs.filter(status='Pending').count()
    in_progress_count = qs.filter(status='In Progress').count()
    resolved_count = qs.filter(status='Resolved').count()
    
    # simple filtering via GET params (optional)
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    
    return render(request, 'requests_list.html', {
        'requests': qs, 
        'user': request.user, 
        'is_my_requests': False,
        'total_count': total_count,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
    })

    
# --- Simple SendGrid example function (HTTP POST) ---
def send_new_request_email(req):
    sg_api_key = getattr(settings, 'SENDGRID_API_KEY', None)
    if not sg_api_key:
        # no key — in dev, skip or log
        return
    url = "https://api.sendgrid.com/v3/mail/send"
    payload = {
      "personalizations": [
        {
          "to": [{"email": settings.IT_TEAM_EMAIL}],
          "subject": f"New IT Request: {req.category} - {req.requester_name}"
        }
      ],
      "from": {"email": settings.DEFAULT_FROM_EMAIL},
      "content": [
        {
          "type": "text/plain",
          "value": f"New request by {req.requester_name}\nDept: {req.department}\nCategory: {req.category}\nDescription:\n{req.description}\nStatus: {req.status}"
        }
      ]
    }
    headers = {
      "Authorization": f"Bearer {sg_api_key}",
      "Content-Type": "application/json"
    }
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        # log or print in dev
        print("Email send failed:", e)

def send_resolution_email(req):
    # Similar implementation: notify IT/admin or requester if you stored email (not in spec)
    pass

@login_required
def user_list(request):
    """
    View to show all registered users - only accessible by staff
    """
    if not request.user.is_staff:
        return HttpResponse("Forbidden. Only administrators can view user list.", status=403)
    
    # Get all users ordered by date joined (newest first)
    users = User.objects.all().order_by('-date_joined')
    
    # Get user counts for statistics
    total_users = users.count()
    staff_users = users.filter(is_staff=True).count()
    active_users = users.filter(is_active=True).count()
    
    # Handle search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Handle status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'staff':
        users = users.filter(is_staff=True)
    elif status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    context = {
        'users': users,
        'total_users': total_users,
        'staff_users': staff_users,
        'active_users': active_users,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'user_list.html', context)

@login_required
def user_update(request, pk):
    """
    Update an existing user - only accessible by staff
    """
    if not request.user.is_staff:
        return HttpResponse("Forbidden. Only administrators can update users.", status=403)
    
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('requests_app:user_list')
    else:
        form = UserRegistrationForm(instance=user)
    
    return render(request, 'user_form.html', {
        'form': form,
        'title': 'Update User',
        'action': 'Update',
        'user_obj': user
    })

@login_required
def user_delete(request, pk):
    """
    Delete a user - only accessible by staff
    """
    if not request.user.is_staff:
        return HttpResponse("Forbidden. Only administrators can delete users.", status=403)
    
    user = get_object_or_404(User, pk=pk)
    
    # Prevent users from deleting themselves
    if request.user.id == user.id:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('requests_app:user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('requests_app:user_list')
    
    return render(request, 'user_confirm_delete.html', {
        'user_obj': user
    })

@login_required
def user_detail(request, pk):
    """
    View user details - only accessible by staff
    """
    if not request.user.is_staff:
        return HttpResponse("Forbidden. Only administrators can view user details.", status=403)
    
    user = get_object_or_404(User, pk=pk)
    
    # Get user's service request statistics
    user_requests = ServiceRequest.objects.filter(requester_name=user.get_full_name() or user.username)
    total_requests = user_requests.count()
    pending_requests = user_requests.filter(status='Pending').count()
    in_progress_requests = user_requests.filter(status='In Progress').count()
    resolved_requests = user_requests.filter(status='Resolved').count()
    
    # Recent requests
    recent_requests = user_requests.order_by('-created_at')[:5]
    
    context = {
        'user_obj': user,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'in_progress_requests': in_progress_requests,
        'resolved_requests': resolved_requests,
        'recent_requests': recent_requests,
    }
    
    return render(request, 'user_detail.html', context)