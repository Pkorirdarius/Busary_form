# AI Agent Instructions for Bursary Application System

## Project Overview
This is a Django-based bursary application management system that handles the entire lifecycle of bursary applications, from submission to approval. The system is designed for high performance and scalability, with optimized database queries and caching.

## Key Architecture Components

### Models (`backend_logic/models.py`)
- `UserProfile`: Extended user profile for applicants
- `BursaryApplication`: Core model for bursary applications with extensive indexing
- `ApplicationStatusLog`: Audit trail for application status changes
- `Document`: Handles file attachments with verification status

### Views Architecture
- Uses class-based views with LoginRequiredMixin for security
- Implements optimized queryset loading with select_related/prefetch_related
- Multi-step form processing in `bursary_apply` view

## Development Workflows

### Local Development
```bash
python manage.py runserver
python manage.py migrate
python manage.py createsuperuser
```

### Database & Performance Considerations
- Uses SQLite in development, configurable for production databases
- Heavy use of database indexes for performance optimization
- Key indexes on: application status, submission date, education level
- Implements caching for templates and queries

### Testing
- Test data generators available in `tests.py`
- Use `get_minimal_valid_data()` for creating test applications
- Run tests with: `python manage.py test backend_logic`

## Project Conventions

### Model Design Patterns
1. Audit Fields:
   - `created_at`, `updated_at` on all models
   - Status tracking with `ApplicationStatusLog`

2. Validation:
   - Use Django validators (RegexValidator, MinValueValidator)
   - Field-level validation in model clean methods
   - Form-level validation in form clean methods

3. Performance:
   - DB indexes on frequently queried fields
   - Composite indexes for common filter combinations
   - Prefetch related data in views to avoid N+1 queries

### File Upload Handling
- Supported formats: PDF, DOC, DOCX, JPG, JPEG, PNG
- Max file size: 5MB
- Files stored in `media/bursary_documents/%Y/%m/`
- Implement verification status tracking for uploaded documents

### Security Practices
- CSRF protection required
- File type validation on upload
- XSS protection headers enabled
- Rate limiting on form submissions
- Secure cookie settings in production

## Integration Points
1. Email Notifications (`settings.py`):
   - Console backend in development
   - SMTP in production
   - Environment variables for configuration

2. Analytics (`analytics.py`):
   - Dashboard view with key metrics
   - CSV export functionality
   - Timeline tracking per application

3. Task Queue (Optional Celery):
   - Configured for background tasks
   - Daily report generation
   - Cleanup of old applications

## Common Development Tasks

### Adding New Fields to Application
1. Add field to `BursaryApplication` model
2. Create migration: `python manage.py makemigrations`
3. Update form in `forms.py`
4. Update admin display in `admin.py`
5. Update templates to display new field

### Implementing Status Changes
1. Use `ApplicationStatusLog` model
2. Include status change reason
3. Trigger appropriate notifications
4. Update analytics data

## Troubleshooting
- Check `logs/bursary.log` for errors
- Use Django Debug Toolbar in development
- Monitor query performance with `.explain()` 
- Review Celery task logs if background tasks fail