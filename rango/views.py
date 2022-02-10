from django.shortcuts import render
from django.http import HttpResponse

from rango.models import Category
from rango.models import Page


from rango.forms import CategoryForm
from django.shortcuts import redirect

from rango.forms import PageForm
from django.urls import reverse


from rango.forms import UserForm, UserProfileForm

from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.decorators import login_required

from datetime import datetime

def index(request):
    
    category_list =  Category.objects.order_by('-likes')[:5]
    page_list =  Page.objects.order_by('-views')[:5]
    context_dict = {}
    # key boldmessage matches to {{ boldmessage }} in the template
    context_dict['boldmessage']='Crunchy, creamy, cookie, candy, cupcake!'
    context_dict['categories']=category_list
    context_dict['pages']=page_list
    # Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.

    visitor_cookie_handler(request)

    
    response = render(request, "rango/index.html", context=context_dict)

    return response


def about(request):
    context_dict={}
    context_dict['boldmessage'] = 'Rango says here is the about page.'
    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']
    return render(request, "rango/about.html", context=context_dict)


def show_category(request,category_name_slug):
    #create a context dictionary which we can pass
    #to the template rendering engine
    context_dict = {}

    try:
        #Can we find a category name slug with the give name?
        #if we cant, then .get() method raises a DoesNotExist exception
        #The .get() method returns one model instance or raises and exception
        category = Category.objects.get(slug=category_name_slug)

        #retrieve all of the associated pages.
        #the filter() will return a list of page objects or an empty list
        pages = Page.objects.filter(category=category)

        #Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        #We also add the category objects from
        #the database to the context dictionary
        #We'll use this in the template to verify that the category exists.
        context_dict['category'] = category
        
    except Category.DoesNotExist:
        #we get here if we didnt find the specified category
        #dont do anything -
        #the template will display "no categort" message
        context_dict['category']=None
        context_dict['pages']=None

    #Go render the response and return it to the client.
    return render(request, 'rango/category.html', context=context_dict)

@login_required
def add_category(request):
    form = CategoryForm()

    if request.method == "POST":
        form = CategoryForm(request.POST)

        #is the form valid?
        if form.is_valid():
            #save new category in database
            form.save(commit=True)
            #redirect user back to index view
            return redirect('/rango/')
        else:
            #invalid form:
            print(form.errors)
    #render form with error messages if any
    return render(request, 'rango/add_category.html', {'form' : form})


@login_required
def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category=None

    if category is None:
        return redirect('/rango/')

    form = PageForm()

    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()

                return redirect(reverse('rango:show_category',
                                        kwargs={'category_name_slug':
                                                category_name_slug}))
        else:
            print(form.errors)
    context_dict = {'form' : form, 'category' : category}
    return render(request, 'rango/add_page.html', context=context_dict)
                                

def register(request):
    #boolean to indicate successful registration
    #False initially
    #changes to true with successful registration
    registered = False


    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit = False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()
            registered = True
        else:
            print(user_form.errors, profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
        
    return render(request, 'rango/register.html',
                  context={'user_form': user_form,
                           'profile_form' : profile_form,
                           'registered' : registered})
    
def user_login(request):
    if request.method == 'POST':
        #use request.POST.get(..) instead of request.POST(..) because this
        #returns None if no value but get returns a KeyError
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request,user)
                return redirect(reverse('rango:index'))
            else:
                return HttpResponse("Invalid login details supplied.")
    else:
        return render(request, 'rango/login.html')


@login_required
def restricted(request):
    return render(request, 'rango/restricted.html')


@login_required
def user_logout(request):
    logout(request)
    return redirect(reverse('rango:index'))

def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request,'visits','1'))

    last_visit_cookie = get_server_side_cookie(request,'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

    if (datetime.now() - last_visit_time).days>0:
        visits = visits + 1;
        request.session['last_visit'] = str(datetime.now())
    else:
        request.session['last_visit'] = last_visit_cookie
        
    request.session['visits'] = visits


def get_server_side_cookie(request,cookie,default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val
