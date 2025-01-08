# inventory/forms.py
from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['file_name', 'name', 'category','rarity','strength', 'agility', 'intelligence', 'stealth', 'speed', 'defence']
