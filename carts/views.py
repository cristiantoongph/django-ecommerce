from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist

def _cart_id(request):
  cart = request.session.session_key
  # if theres no cart in session
  if not cart:
    cart = request.session.create()
  return cart

def add_cart(request, product_id):
  product = Product.objects.get(id=product_id)#get product
  product_variation = []
  if request.method == 'POST':
    #loop tru variations(color and size)
    for item in request.POST:
      key = item
      value = request.POST[key]
      # check if key and value matches Variation Model methods (color and size)
      try:
        variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
        product_variation.append(variation)
      except:
        pass

  #if cart exists get the card in session else create cart object
  try:
    cart = Cart.objects.get(cart_id=_cart_id(request)) #get the cart using the cart_id present in the session
  except Cart.DoesNotExist:
    cart = Cart.objects.create(
      cart_id=_cart_id(request)
    )
  cart.save()

  # Check if cart item exists or not:
  is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()

  # if cartItem already available in the cart/cart session
  # cart with product and add cart qty
  if is_cart_item_exists:
    cart_item = CartItem.objects.filter(product=product, cart=cart)
    # existing variations -> database
    # current variation -> product_variation
    # item id -> database
    ex_var_list = []
    id = []
    #IF THE CURRENT VARIATION IS INSIDE THE EXISTING VARIATION increase qty of the item
    for item in cart_item:
      existing_variation = item.variations.all()
      ex_var_list.append(list(existing_variation))
      id.append(item.id)
    print(ex_var_list)
    if product_variation in ex_var_list:
      # increase the cart item quantity
      index = ex_var_list.index(product_variation)
      item_id = id[index]
      item = CartItem.objects.get(product=product, id=item_id)
      item.quantity += 1
      item.save()
    else:
      #create new cart item
      item = CartItem.objects.create(product=product, quantity=1, cart=cart)
      # add variation in the cart item
      if len(product_variation) > 0:
        item.variations.clear()
        item.variations.add(*product_variation)
      item.save()
  else:
    #if cartitem not exist create new cart item
    cart_item = CartItem.objects.create(
      product=product,
      quantity=1,
      cart=cart,
    )
    # add variation in the cart item
    if len(product_variation) > 0:
      cart_item.variations.clear()
      cart_item.variations.add(*product_variation)
    cart.save()
  return redirect('cart')

def remove_cart(request, product_id, cart_item_id):
  cart = Cart.objects.get(cart_id=_cart_id(request))
  product = get_object_or_404(Product, id=product_id)
  try:
    cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    # qty is greater than 1 decrement qty
    if cart_item.quantity > 1:
      cart_item.quantity -= 1
      cart_item.save()
    else:
      cart_item.delete()
  except:
    pass
  return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
  cart = Cart.objects.get(cart_id=_cart_id(request))
  product = get_object_or_404(Product, id=product_id)
  cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
  cart_item.delete()
  return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
  try:
    tax = 0
    grand_total = 0
    cart = Cart.objects.get(cart_id=_cart_id(request))
    cart_items = CartItem.objects.filter(cart=cart, is_active=True)
    for cart_item in cart_items:
      total += (cart_item.product.price * cart_item.quantity)
      quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax
  except ObjectDoesNotExist:
    pass

  context = {
    'total': total,
    'quantity': quantity,
    'cart_items': cart_items,
    'tax': tax,
    'grand_total': grand_total
  }

  return render(request, 'store/cart.html', context)