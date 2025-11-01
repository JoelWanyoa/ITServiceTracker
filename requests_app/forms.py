from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import  ResolutionStep, ServiceRequest

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    department = forms.CharField(max_length=100, required=True, help_text="Department the user belongs to")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'department', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create or update UserProfile
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.department = self.cleaned_data['department']
            profile.save()
        return user

class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['department', 'category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows':4})
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Make department optional, but pre-populate if user has a profile
        self.fields['department'].required = False
        if user and hasattr(user, 'profile') and user.profile.department:
            self.fields['department'].initial = user.profile.department

class ResolutionStepForm(forms.ModelForm):
    class Meta:
        model = ResolutionStep
        fields = ['step_number', 'description']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-input block w-full rounded-lg border-gray-300 shadow-sm px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Describe the step taken to resolve the issue...'
            }),
            'step_number': forms.NumberInput(attrs={
                'class': 'form-input block w-full rounded-lg border-gray-300 shadow-sm px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'min': 1
            })
        }

class ResolutionStepInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        step_numbers = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                step_number = form.cleaned_data.get('step_number')
                if step_number in step_numbers:
                    form.add_error('step_number', 'Step numbers must be unique.')
                step_numbers.append(step_number)
