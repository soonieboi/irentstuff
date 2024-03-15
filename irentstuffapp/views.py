from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives    
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone 
from django.db.models import Count
from django.conf import settings
from .models import Item, Rental, Message, Review
from .forms import ItemForm, ItemEditForm, RentalForm, MessageForm, ItemReviewForm


def index(request):
    return HttpResponse("Index")

def items_list(request):
    # Filter items with is_available=True
    available_items = Item.objects.all().order_by('created_date')
    # Apply additional filters based on request.GET parameters

    # Pagination (optional)
    paginator = Paginator(available_items, 10) # 10 items per page
    page_obj = paginator.page(1)

    if (request.GET.get('page')):
        page_number = request.GET.get('page')
        page_obj = paginator.page(page_number)

    search_query = request.GET.get('search', '')

    if request.user.is_authenticated:
        if request.resolver_match.url_name == 'items_list_my':
            items = Item.objects.filter(owner=request.user.id).all()
        else:
            items = Item.objects.exclude(owner=request.user.id).all() 
    else:
        items = Item.objects.all() 

    if search_query:
        items = items.filter(title__contains=search_query).all()

    if not items:
        no_items_message = True
    else:
        no_items_message = None

    return render(request, 'irentstuffapp/items.html', {'items': items, 'no_items_message': no_items_message, 'searchstr':search_query,
     'mystuff': request.resolver_match.url_name == 'items_list_my', 'page' : page_obj})

@login_required
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

@login_required
def add_review(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    user = request.user
    form = ItemReviewForm(user, item, request.POST or None)
    
    if request.method == 'POST':
        if form.is_valid():
            review = form.save(commit=False)
            review.author = user
            review.created_date = timezone.now()
            review.save()
            
            return redirect('item_detail', item_id=item_id)  # Redirect to item detail page
        # else:
        #     raise Exception("Your review cannot be submitted.")

    return render(request, 'irentstuffapp/review_add.html', {'form': form, 'item':item})

def item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    reviews = Review.objects.filter(rental__item=item)
    is_owner = request.user == item.owner
    msgshow = True

    if is_owner:
        #check if there are any messages related to this item
        item_messages = Message.objects.filter(item=item)
        if not item_messages:
            msgshow = False

    active_rental = False
    accept_rental = False
    cancel_rental = False
    complete_rental = False
    renter = None
    active_rentals_obj = None
    make_review = False

    if request.user.is_authenticated:

        if item.owner == request.user:
            # Check if there are active rentals for this item
            active_rentals_obj = Rental.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled").first()
            if active_rentals_obj:
                renter = active_rentals_obj.renter

                #can cancel?
                if active_rentals_obj.status=='pending':
                    cancel_rental = True
                #can complete?
                elif active_rentals_obj.status=='confirmed':
                    complete_rental = True

        else:
            # Check if there is a rental for this item related to this user
            active_rentals_obj = Rental.objects.filter(item=item, renter = request.user).exclude(status="completed").exclude(status="cancelled").first()
            if active_rentals_obj:

                renter = active_rentals_obj.renter

                #can accept?
                # Check if there is a rental offer for this item - pending - before start_date
                #accept_rental_obj = active_rentals_obj.filter(status='pending', start_date__gt=timezone.now()).first()
                #if accept_rental_obj:
                if active_rentals_obj.status=='pending':
                    if active_rentals_obj.start_date>timezone.now().date():
                        accept_rental = True
                    else:
                        active_rentals_obj = None

            #check if there are any completed rentals that user may want to review
            review_obj =  Rental.objects.filter(renter=request.user, item=item, status='completed')
            if review_obj:
                make_review = True
                
    return render(request, 'irentstuffapp/item_detail.html', {'item': item, 'is_owner': is_owner, 'make_review': make_review, 'active_rental': active_rentals_obj, 'accept_rental': accept_rental, 'complete_rental': complete_rental, 'cancel_rental': cancel_rental, 'renter': renter, 'mystuff': request.resolver_match.url_name == 'items_list_my', 'msgshow':msgshow, 'reviews':reviews})

@login_required
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

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is the creator of the item
    if request.user != item.owner:
        # Optionally, you can handle unauthorized access here
        return redirect('item_detail', item_id=item.id)

    # Delete the item
    try: 
        item.delete()
    except Exception as e:
        messages.error(request, 'Error deleting item: ' + str(e))
    return redirect('items_list')  # Redirect to the items list page or another appropriate page


@login_required
def item_messages(request, item_id, userid=0):

    item = get_object_or_404(Item, pk=item_id)
    
    #owner view of messages from every user who enquired
    if userid == 0 and item.owner == request.user:

        # Group messages by enquiring_user_id and count the number of messages for each user
        grouped_messages = Message.objects.filter(item=item).values('enquiring_user','enquiring_user__username').annotate(message_count=Count('id'))

        return render(request, 'irentstuffapp/item_messages_list.html', {'item': item, 'grouped_messages': grouped_messages})
    
    else:

        #enquiring_user = User.objects.filter(id=userid).first()

        if item.owner == request.user:
            enquiring_user = User.objects.filter(id=userid).first()
        else:
            enquiring_user = request.user
        
        if request.method == 'POST':
            message_form = MessageForm(request.POST)
            if message_form.is_valid():
                print('valid')
                message = message_form.save(commit=False)
                message.sender = request.user
                if request.user == item.owner:
                    message.recipient = enquiring_user
                else:
                    message.recipient = item.owner

                message.item = item
                message.enquiring_user = enquiring_user
                message.subject = 'message'
                message.timestamp = timezone.now()
                message.save()

                subject = 'iRentStuff.app - You have a message'
                html_message = render_to_string('emails/enquiry_received_email.html', {'message': message})
                plain_message = strip_tags(html_message)
                email_from = settings.DEFAULT_FROM_EMAIL

                email = EmailMultiAlternatives(
                    subject,
                    plain_message,
                    email_from,
                    [message.recipient.email],
                )
                email.attach_alternative(html_message, "text/html")
                email.send()


                if request.user == item.owner: 
                    return redirect('item_messages', item_id=item.id, userid=enquiring_user.id)
                    
                else:
                    return redirect('item_messages_list', item_id=item.id)

                #messages.success(request, 'Rental added successfully!')
                #return redirect('item_detail', item_id=item.id)
                #return redirect(reverse('current_url_name'))
                #return render(request, 'irentstuffapp/item_messages.html', {'item': item, 'enquiring_user':enquiring_user.username,'item_messages': item_messages, 'message_form': message_form})

                #item_messages = Message.objects.filter(item=item, enquiring_user = userid).order_by('timestamp')

                #return render(request, 'irentstuffapp/item_messages.html', {'item': item, 'enquiring_user':enquiring_user.username,'item_messages': item_messages, 'message_form': message_form})
        else:
            message_form = MessageForm(initial={'item': item, 'recipient': item.owner})

        #set messages to is_read
        item_incoming_msgs = Message.objects.filter(item=item, enquiring_user = enquiring_user, is_read = False).exclude(sender = request.user.id)
        for itmmsg in item_incoming_msgs:
            itmmsg.is_read = True
            itmmsg.save()

        active_rentals = False
        accept_rental = False
        if item.owner == request.user:
            # Check if there are active rentals for this item
            active_rentals_obj = Rental.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled").first()
            if active_rentals_obj:
                active_rentals = True
        else:
            # Check if there is a rental offer for this item - pending - before start_date
            accept_rental_obj = Rental.objects.filter(item=item, renter = request.user, status='pending', start_date__gt=timezone.now()).first()
            if accept_rental_obj:
                accept_rental = True

        item_messages = Message.objects.filter(item=item, enquiring_user = enquiring_user).order_by('timestamp')
        return render(request, 'irentstuffapp/item_messages.html', {'item': item, 'enquiring_user':enquiring_user.username,'item_messages': item_messages, 'message_form': message_form, 'active_rentals': active_rentals, 'accept_rental':accept_rental})

@login_required
def inbox(request):

    # Group messages by enquiring_user_id and count the number of messages for each user
    grouped_messages = Message.objects.filter(recipient = request.user.id).values('enquiring_user','enquiring_user__username','item__id', 'item__title').annotate(message_count=Count('id'))

    return render(request, 'irentstuffapp/inbox.html', {'grouped_messages': grouped_messages})

@login_required
def add_rental(request, item_id, username=""):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is the creator of the item
    if request.user != item.owner:
        # Optionally, you can handle unauthorized access here
        return redirect('item_detail', item_id=item.id)

    if request.method == 'POST':
        form = RentalForm(request.POST)
        
        # Check if there are active rentals for the item
        active_rentals = Rental.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled")
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

            renterid = form['renterid'].value()

            rental = form.save(commit=False)
            
            rentaluser = User.objects.filter(username=renterid).first()
            rental.renter = rentaluser
            
            rental.item = item  # Set the item for the rental
            rental.owner = request.user  # Set the owner to the logged-in user
            rental.pending_date = timezone.now()
            rental.status = 'pending' 
            
            rental.save()


            subject = 'iRentStuff.app - You added a Rental'
            html_message = render_to_string('emails/rental_added_email.html', {'rental': rental, 'item':item})
            plain_message = strip_tags(html_message)
            email_from = settings.DEFAULT_FROM_EMAIL

            email = EmailMultiAlternatives(
                subject,
                plain_message,
                email_from,
                [request.user.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()

            subject2 = 'iRentStuff.app - You have a Rental Offer'
            html_message2 = render_to_string('emails/rental_added_email2.html', {'rental': rental, 'item':item})

            plain_message2 = strip_tags(html_message2)

            email2 = EmailMultiAlternatives(
                subject2,
                plain_message2,
                email_from,
                [rentaluser.email],
            )
            email2.attach_alternative(html_message2, "text/html")
            email2.send()

            return redirect('item_detail', item_id=item.id)

    else:
        form = RentalForm()
        if username:
            form['renterid'].initial = username
        

    return render(request, 'irentstuffapp/rental_add.html', {'form': form, 'item': item})

@login_required
def accept_rental(request, item_id):
    item = get_object_or_404(Item, pk=item_id)


    # Check if the logged-in user is renter
    accept_rental_obj = Rental.objects.filter(item=item, renter = request.user, status='pending', start_date__gt=timezone.now()).first()
    if accept_rental_obj:
        accept_rental_obj.status = 'confirmed'
        accept_rental_obj.confirm_date = timezone.now()
        accept_rental_obj.save()

        subject = 'iRentStuff.app - you have a Rental Acceptance'
        html_message = render_to_string('emails/rental_confirmed_email.html', {'rental': accept_rental_obj, 'item':item})
        plain_message = strip_tags(html_message)
        email_from = settings.DEFAULT_FROM_EMAIL

        email = EmailMultiAlternatives(
            subject,
            plain_message,
            email_from,
            [item.owner.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()

        subject2 = 'iRentStuff.app - You accepted a Rental Offer'
        html_message2 = render_to_string('emails/rental_confirmed_email2.html', {'rental': accept_rental_obj, 'item':item})

        plain_message2 = strip_tags(html_message2)

        email2 = EmailMultiAlternatives(
            subject2,
            plain_message2,
            email_from,
            [request.user.email],
        )
        email2.attach_alternative(html_message2, "text/html")
        email2.send()

    return redirect('item_detail', item_id=item.id)

@login_required
def complete_rental(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is owner and status is confirmed
    complete_rental_obj = Rental.objects.filter(item=item, owner = request.user, status='confirmed').first()
    if complete_rental_obj:
        complete_rental_obj.status = 'completed'
        complete_rental_obj.complete_date = timezone.now()
        complete_rental_obj.save()

        subject = 'iRentStuff.app - you have set a rental to Complete'
        html_message = render_to_string('emails/rental_completed_email.html', {'rental': complete_rental_obj,})
        plain_message = strip_tags(html_message)
        email_from = settings.DEFAULT_FROM_EMAIL

        email = EmailMultiAlternatives(
            subject,
            plain_message,
            email_from,
            [item.owner.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()

    return redirect('item_detail', item_id=item.id)

@login_required
def cancel_rental(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is owner and status is confirmed
    cancel_rental_obj = Rental.objects.filter(item=item, owner = request.user, status='pending').first()
    if cancel_rental_obj:
        cancel_rental_obj.status = 'cancelled'
        cancel_rental_obj.cancelled_date = timezone.now()
        cancel_rental_obj.save()

        subject = 'iRentStuff.app - you have cancelled a rental'
        html_message = render_to_string('emails/rental_cancelled_email.html', {'rental': cancel_rental_obj,})
        plain_message = strip_tags(html_message)
        email_from = settings.DEFAULT_FROM_EMAIL

        email = EmailMultiAlternatives(
            subject,
            plain_message,
            email_from,
            [item.owner.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()

    return redirect('item_detail', item_id=item.id)

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
            email_from = settings.DEFAULT_FROM_EMAIL

            email = EmailMultiAlternatives(
                subject,
                plain_message,
                email_from,
                [email],
            )
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

@login_required
def logout_user(request):
    logout(request)
    return redirect('/')
    