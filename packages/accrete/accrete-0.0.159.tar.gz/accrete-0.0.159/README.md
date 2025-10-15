# Multi Tenant App for Django
Shared approach multi tenancy system for Django Projects.

## Installation
Add accrete to installed_apps and accrete.middleware.TenantMiddleware to 
middleware  

## TenantModel
Base Model with a ForeignKey to tenant.Tenant and objects set to
accrete.models.TenantManager

## Basic Usage

```python
from accrete.models import TenantModel

class MyModel(TenantModel):
    ...
```
---
Each user can be a member of multiple Tenants, just add them to tenant.members.  
This is necessary when using the Mixins and Middleware provided by this app.

## Middleware
###### tenant.middleware.TenantMiddleware
This Middleware adds the Tenant(request.tenant) and 
Member(request.member) objects as attributes to the request
object and sets a cookie with the tenant_id.

If the user is a member of multiple tenants, the request is parsed for a 
tenant_id in this order.

- The "tenant" parameter in the POST data
- The Header X-TENANT-ID
- The "tenant_id" URL Parameter in the GET data
- The "tenant_id" cookie previously set by the Middleware

If no tenant could be assigned the two attributes are set to None.  
Additionally, the user is checked for membership of the found tenant.

Adds the tenant to the POST data.

The Middleware must be added 
to the MIDDLEWARE setting after your authentication Middleware as it needs 
access to request.user.is_authenticated().

## Views
### Mixins
###### tenant.views.TenantRequiredMixin 
Adds tenant and optionally access right checks to the dispatch method.  
This Mixin is meant as a substitute to 
django.contrib.auth.mixins.LoginRequiredMixin as TenantRequiredMixin inherits
LoginRequiredMixin.  

Adds the member_access_groups attribute to the view. This attribute can be a
list of codes from the tenant.models.AccessGroup model. If present, the 
member must be part of one of the listed groups to access the view. 
Failing checks are handled in a similar way as in LoginRequiredMixin. 


### Decorators
###### tenant.decorators.tenant_required
Substitute for django.contrib.auth.decorators.login_required  
Checks if a tenant is set on the request and redirects to the 
TENANT_MISSING_URL specified in the settings.

The decorator itself is wrapped by login_required and can pass the arguments
redirect_field_name and login_url to login_required.

## Forms
###### tenant.forms.Form
Form class that adds the tenant as a field and filters the queryset of every
field that has a queryset attribute.

###### tenant.forms.ModelForm
Same behaviour as tenant.forms.Form.

## Settings
Custom settings
- TENANT_MISSING_URL  
Redirect to this URL when no tenant could be set for an authenticated user.


- TENANT_MEMBER_NOT_AUTHORIZED_URL  
Redirect to this URL when a member tries to access a URL without having the 
needed access rights.
