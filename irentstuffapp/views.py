from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Item, Rental
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives    
from django.contrib.auth.decorators import login_required
from .forms import ItemForm, ItemEditForm
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone 



def index(request):
    return HttpResponse("Index")

#def get_available_items(request):
def items_list(request):
    # Filter items with is_available=True
    #available_items = Item.objects

    

    # Apply additional filters based on request.GET parameters

    # Pagination (optional)
    '''paginator = Paginator(available_items, 10) # 10 items per page
    if (request.GET.get('page')):
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Serialize items
        serializer = ItemSerializer(page_obj.object_list, many=True)
    '''

    if request.user.is_authenticated:
        if request.resolver_match.url_name == 'items_list_my':
            items = Item.objects.filter(owner=request.user.id).all()
        else:
            items = Item.objects.exclude(owner=request.user.id).all() 
    else:
        items = Item.objects.all() 

    if not items:
        no_items_message = 'You have no items.'
    else:
        no_items_message = None

    return render(request, 'irentstuffapp/items.html', {'items': items, 'no_items_message': no_items_message, 'mystuff': request.resolver_match.url_name == 'items_list_my'})

def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user  # Set the item's creator to the logged-in user
            item.created_date = timezone.now() 
            item.save()
            return redirect('item_detail', item_id=item.id)  # Redirect to item detail page
    else:
        form = ItemForm()

    return render(request, 'irentstuffapp/item_add.html', {'form': form})

def item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    is_owner = request.user == item.owner
    active_rental = Rental.objects.filter(item=item, end_date__gt=timezone.now()).exclude(status="completed").exclude(status="cancelled").first()
    if active_rental:
        renter = active_rental.renter
    else:
        renter = None
    return render(request, 'irentstuffapp/item_detail.html', {'item': item, 'is_owner': is_owner, 'active_rental': active_rental, 'renter': renter, 'mystuff': request.resolver_match.url_name == 'items_list_my'})

def edit_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    
    # Check if the user is the owner of the item
    if request.user != item.owner:
        # Optionally, you can handle unauthorized access here
        return redirect('item_detail', item_id=item.id)

    if request.method == 'POST':
        form = ItemEditForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('item_detail', item_id=item.id)
    else:
        form = ItemEditForm(instance=item)

    return render(request, 'irentstuffapp/item_edit.html', {'item': item, 'form': form})

def delete_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is the creator of the item
    if request.user != item.owner:
        # Optionally, you can handle unauthorized access here
        return redirect('item_detail', item_id=item.id)

    # Delete the item
    item.delete()
    return redirect('items_list')  # Redirect to the items list page or another appropriate page

# myrentalapp/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import Item, Rental
from .forms import RentalForm

def add_rental(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    

    # Check if the logged-in user is the creator of the item
    if request.user != item.owner:
        # Optionally, you can handle unauthorized access here
        return redirect('item_detail', item_id=item.id)

    if request.method == 'POST':
        form = RentalForm(request.POST)
        
        

        # Check if there are active rentals for the item
        active_rentals = Rental.objects.filter(item=item, end_date__gt=timezone.now()).exclude(status="completed").exclude(status="cancelled")
        if active_rentals.exists():
            messages.error(request, 'There are active rentals for this item. You cannot add a new rental.')
            return redirect('item_detail', item_id=item.id)

        # Check if the logged-in user is the creator, owner, or renter of the item
        if request.user == form['renterid']:
            # Optionally, you can handle unauthorized access here
            messages.error(request, 'You cannot rent your own item.')
            return redirect('item_detail', item_id=item.id)

        #form['status'] = 'pending'
        if form.is_valid():

            print('valid')

            renterid = form['renterid'].value()

            rental = form.save(commit=False)
            
            rentaluser = User.objects.filter(username=renterid).first()
            rental.renter = rentaluser
            
            rental.item = item  # Set the item for the rental
            rental.owner = request.user  # Set the owner to the logged-in user
            rental.status = 'pending' 
            
            rental.save()
            return redirect('item_detail', item_id=item.id)
        else:
            print('invalid')
    else:
        form = RentalForm()
        '''form.fields['status'].initial = ['pending']
        form.fields['owner'].initial = [request.user.id]
        form.fields['item'].initial = [item.id]'''
        

    return render(request, 'irentstuffapp/rental_add.html', {'form': form, 'item': item})

def check_user_exists(request, username):
    user_exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': user_exists})

def register(request):
    if request.method=='POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        firstname = request.POST.get('fname')
        lastname = request.POST.get('lname')
        username = request.POST.get('uname')
        if User.objects.filter(email=email).exists():
            messages.warning(request,'User with this email already exists')
            return redirect('register')
        else:
            user = User(email=email,password=password,first_name=firstname,
            last_name=lastname,username=username)
            user.set_password(password)
            user.save()

            subject = 'Welcome to iRentStuff.app - Your Account Registration is Successful!'

            html_message = render_to_string('emails/welcome_email.html', {'user_name': username})
            plain_message = strip_tags(html_message)

            #message = render_to_string('emails/welcome_email.txt', {'user_name': username})
            #message = f'Hi, welcome to iRentStuff. Thank you for joining us!'
            #plain_message = strip_tags(message)

            email_from = 'admin@irentstuff.app' 

            email = EmailMultiAlternatives(
                subject,
                plain_message,
                email_from,  # Replace with your "from" email address
                [email],
            )
            #email.content_subtype = 'html'  # Set the content type to HTML
            email.attach_alternative(html_message, "text/html")
            email.send()

            messages.success(request, 'Thank you for your registration! You may log in now')
            return redirect('/login')
    return render(request,'irentstuffapp/register.html')

def login_user(request):
    if request.method=='POST':
        username = request.POST['uname']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.warning(request,'Invalid Credentials')
            return redirect('login')
    return render(request,'irentstuffapp/login.html')

def logout_user(request):
    logout(request)
    return redirect('/')
    