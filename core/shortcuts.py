from django.views import View
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from admin_strong.configuration import NAVBAR, HELP_LINK
from django.urls import reverse
from django.db.models import Q
from admin_strong.configuration import RELATED_MODEL_URLS


class BaseView(View):
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated or not request.user.is_superuser:
            return HttpResponseRedirect('/login')
        return super(BaseView, self).dispatch(request, *args, **kwargs)
    
    def get_context(self):
        context = {
            'navbar': NAVBAR,
            'help': HELP_LINK,
        }
        return context

   
class SoloView(BaseView):
    
    form = None
    model = None
    title = ""
    
    def get_context(self, form=True):
        data = super(SoloView, self).get_context()
        if form:
            data['form'] = self.form(instance=self.model.get_solo())
        data['title'] = self.title
        data['success'] = 'success' in self.request.GET
        return data
        
    def get(self, request):
        return render(request, 'admin_strong/solo.html', self.get_context())
    
    def post(self, request):
        context = self.get_context(False)
        
        form = self.form(request.POST, instance=self.model.get_solo())
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('?success=true')
        context['form'] = form 
        context['error'] = True
        
        return render(request, 'admin_strong/solo.html', context)

    
class ListView(BaseView):
    model = None
    fields = ()
    count = 20
    order_by = ('-id', 'id')
    search_fields = ()
    title = ""
    detail_url = ""
    
    def get_page(self):
        return int(self.request.GET.get('page', 1)) - 1
    
    def filter(self):
        if not self.request.GET.get('search', None):
            return []
        
        STATUSES = {}
        if list(filter(lambda a: a.name == 'status', self.model._meta.fields)):
            for status in self.model.STATUS:
                STATUSES[status[1]] = str(status[0])
            
        l = []
        for field in self.search_fields:
            if field == 'status':
                l.append({'status': STATUSES.get(self.request.GET['search'])})
            else:
                l.append({"{}__icontains".format(field):self.request.GET['search']})
        return l
            
    def get_queryset(self):
        queryset = self.model.objects.all()
        
        my_filter = Q()
        for filter in self.filter():
            my_filter |= Q(**filter)
            
        queryset = queryset.filter(my_filter)
        
        queryset = queryset.order_by(self.request.GET.get('order_by', self.order_by[0]))
        page = self.get_page()
        start = self.count*page
        end = start + self.count
        
        count = queryset.count()
        
        queryset = queryset[start:end]
        data = []
        for item in queryset:
            a = {}
            for field in self.fields:
                if getattr(self, 'get_{}'.format(field), None):
                    a[field] = getattr(self, 'get_{}'.format(field))(item)
                else:
                    a[field] = getattr(item, field, "")
            data.append(a)
        
        return data, page+1, count / self.count, self.count, count
    
    def get_columns(self):
        data = []
        for column in self.fields:
            data.append(list(filter(lambda a: a.name == column, self.model._meta.fields))[0].verbose_name)
        return data
    
    def order_by_list(self):
        data = {
            'active': self.request.GET.get('order_by', ''),
            'list': [],
        }
        for order in self.order_by:
            data['list'].append({
                'down': '-' in order,
                'value': order,
                'name': list(filter(lambda a: a.name == order.replace('-', ''), self.model._meta.fields))[0].verbose_name,
            })
        return data
    
    def get_context(self):
        data = super(ListView, self).get_context()
        data['search'] = self.request.GET.get('search', "")
        data['objects'], data['page'], data['pages'], data['count'], data['count_objects'] = self.get_queryset()
        data['fields'] = self.fields
        data['columns'] = self.get_columns()
        data['next'] = data['page'] * self.count < data['count_objects']
        data['title'] = self.title
        data['showed_values'] = len(data['objects'])
        data['order_by'] = self.request.GET.get('order_by', self.order_by[0])
        data['order_by_objects'] = self.order_by_list()
        data['detail'] = self.detail_url
        return data
        
    def get(self, request):
        return render(request, 'admin_strong/list.html', self.get_context()) 


class DetailView(BaseView):
    model = None
    form = None
    readonly = False
    back = ""
    title = ""
    delete = False
    readonly_fields = ()
    info = ""
    
    def get_object(self):
        return self.model.objects.filter(id=self.pk).first()
    
    def get_select_objects(self):
        data = {}
        for field in self.form().visible_fields():
            field_model = list(filter(lambda a: a.name == field.name, self.model._meta.fields))[0]
            if field_model.choices:
                data[field.name] = [
                    {'value': choice[0], 'name': choice[1]} for choice in field_model.choices
                ]
        return data
    
    def foreign_key(self):
        data = {}
        for field in self.form().visible_fields():
            field_model = list(filter(lambda a: a.name == field.name, self.model._meta.fields))[0]
            if field_model.related_model:
                data[field.name] = {
                    'url': RELATED_MODEL_URLS.get(field_model.related_model, '/'),
                    'name': field_model.related_model._meta.verbose_name,
                }
        return data
    
    def boolean_fields(self):
        data = []
        for field in self.form().visible_fields():
            if type(field.value()) == bool:
                data.append(field.name)
        return data
    
    def get_context(self, form=True):
        data = super(DetailView, self).get_context()
        self.object = self.get_object()
        data['object'] = self.object 
        if not self.object:
            return data
        
        if form:
            data['form'] = self.form(instance=self.object)
            
        data['back'] = "/" if self.back == "" else reverse(self.back)
        data['title'] = self.title
        data['readonly_fields'] = self.readonly_fields
        data['delete'] = self.delete
        data['success'] = 'success' in self.request.GET
        data['readonly'] = self.readonly
        data['select'] = self.get_select_objects()
        data['foreign_key'] = self.foreign_key()
        data['boolean'] = self.boolean_fields()
        data['info'] = self.info
        
        return data
    
    def post(self, request, pk):
        if self.readonly:
            return HttpResponse('404')
        self.pk = pk
                
        context = self.get_context(False)
        
        if not self.object:
            return HttpResponse('404')
        
        if 'delete' in request.POST:
            self.object.delete()
            return HttpResponseRedirect(reverse(self.back))
        
        form = self.form(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('?success=true')
        context['form'] = form
        context['error'] = True
        
        return render(request, 'admin_strong/detail.html', context)
    
    def get(self, request, pk):
        self.pk = pk
        return render(request, 'admin_strong/detail.html', self.get_context())
  
  
class CardView(BaseView):
    model = None
    title = ""
    active_field = ""
    title_field = ""
    detail_url = ""
    info_fields = ()
    display_views = ()
    create_url = ""
    
    def get_queryset(self):
        queryset = self.model.objects.all().order_by('-id')
        data = []
        for item in queryset:
            data.append({
                'id': item.id,
                'title': getattr(item, self.title_field),
                'active': getattr(item, self.active_field),
                'info': [
                    {
                        'name': list(filter(lambda a: a.name == field, self.model._meta.fields))[0].verbose_name,  
                        'value': getattr(item, f'get_{field}_display')() if field in self.display_views else getattr(item, field),
                    } for field in self.info_fields
                ],
                'url': reverse(self.detail_url, kwargs={'pk': item.id}) if self.detail_url else ""
            })
        return data
    
    def get_context(self):
        data = super(CardView, self).get_context()
        data['objects'] = self.get_queryset()
        data['title'] = self.title
        data['detail_url'] = self.detail_url
        data['create_url'] = reverse(self.create_url) if self.create_url else None
        return data
    
    def post(self, request):
        object = self.model.objects.filter(id=int(request.POST['id']))
        if not object:
            return HttpResponseRedirect(request.path)
        object = object.first()
        setattr(object, self.active_field, not getattr(object, self.active_field))
        object.save(update_fields=(self.active_field,))
        return HttpResponseRedirect(request.path)
        
    def get(self, request):
        return render(request, 'admin_strong/card.html', self.get_context())

 
class CreateView(BaseView):
    model = None
    form = None
    back = ""
    title = ""
    info = ""
    
    def get_select_objects(self):
        data = {}
        for field in self.form().visible_fields():
            field_model = list(filter(lambda a: a.name == field.name, self.model._meta.fields))[0]
            if field_model.choices:
                data[field.name] = [
                    {'value': choice[0], 'name': choice[1]} for choice in field_model.choices
                ]
        return data
    
    def foreign_key(self):
        data = {}
        for field in self.form().visible_fields():
            field_model = list(filter(lambda a: a.name == field.name, self.model._meta.fields))[0]
            if field_model.related_model:
                data[field.name] = {
                    'url': RELATED_MODEL_URLS.get(field_model.related_model, '/'),
                    'name': field_model.related_model._meta.verbose_name,
                }
        return data
    
    def get_context(self, form=True):
        data = super(CreateView, self).get_context()
        
        if form:
            data['form'] = self.form()
            
        data['back'] = reverse(self.back) if self.back else ""
        data['title'] = self.title
        data['success'] = 'success' in self.request.GET
        data['select'] = self.get_select_objects()
        data['foreign_key'] = self.foreign_key()
        data['info'] = self.info
        
        return data
    
    def post(self, request): 
        context = self.get_context(False)
        
        form = self.form(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(context['back'])
        context['form'] = form
        context['error'] = True
        
        return render(request, 'admin_strong/create.html', context)
    
    def get(self, request):
        return render(request, 'admin_strong/create.html', self.get_context())
  

class ListExtendedView(ListView):
    
    create_form = None
    
    def get_select_objects(self):
        data = {}
        for field in self.create_form().visible_fields():
            field_model = list(filter(lambda a: a.name == field.name, self.model._meta.fields))[0]
            if field_model.choices:
                data[field.name] = [
                    {'value': choice[0], 'name': choice[1]} for choice in field_model.choices
                ]
                
        return data
    
    def get_context(self, form=True):
        data = super(ListExtendedView, self).get_context()
        if form:
            data['form'] = self.create_form()
        data['select'] = self.get_select_objects()
        data['success'] = 'success' in self.request.GET
        return data
    
    def get(self, request):
        return render(request, 'admin_strong/extended_list.html', self.get_context())
    
    def post(self, request):
        context = self.get_context(False)
        
        form = self.create_form(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('?success=true')
        context['form'] = form
        context['error'] = True
        
        return render(request, 'admin_strong/extended_list.html', context)