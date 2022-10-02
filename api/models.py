from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from utils.authentication import AuthToken
from utils.email import Email


# Create your models here.
class User(AbstractUser):
    is_verified = models.BooleanField(default=False)

    @property
    def token(self):
        if not self.is_verified:
            return None
        return AuthToken.token(user_id=self.id)

    def save(self, *args, **kwargs) -> None:
        return super().save(*args, **kwargs)

    class Meta:
        db_table = "user"


class DJBaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("id",)

    def __str__(self):
        return f"{self.__class__.__name__}{self.pk}"


class Book(DJBaseModel):
    """Inventory item"""

    class Meta:
        db_table = "book"

    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    author = models.CharField(max_length=10)


class CartItem(DJBaseModel):
    """Shopping item"""

    class Meta:
        db_table = "cart_item"

    user = models.ForeignKey("api.User", on_delete=models.CASCADE)
    book = models.ForeignKey("api.Book", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    ordered = models.BooleanField(default=False)

    @property
    def total_price(self) -> float:
        return self.item.price * self.quantity

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"  # noqa


class Cart(DJBaseModel):
    """Shopping cart"""

    class Meta:
        db_table = "cart"

    is_ordered = models.BooleanField(default=False)
    user = models.ForeignKey("api.User", on_delete=models.CASCADE)
    cart_items = models.ManyToManyField("api.CartItem")

    @property
    def total_price(self):
        return sum([item.total_price for item in self.cart_items.all()])


# signals
@receiver(post_save, sender="api.User")
def mail_verify_user(created: bool, instance: User, **kwargs) -> None:
    if created:
        Email.verify_user(
            payload={"username": instance.username, "user_id": instance.pk},
            recipient=instance.email,
        )
