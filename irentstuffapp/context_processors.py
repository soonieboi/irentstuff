from .models import Category  

def category_list(request):
    """Context processor to add the list of categories to every context."""
    return {'categories': Category.objects.all()}
