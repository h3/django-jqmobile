# -*- coding: utf-8 -*-

import re, os
from django import template
from django.conf import settings
from django.utils.safestring import SafeString
from django.utils.translation import gettext as _
from django.core.urlresolvers import reverse

register = template.Library()

def form_flipswitch(field):
    if field.field.value() == True:
        checked = ' selected="selected"'
        unchecked = ''
    else:
        checked = ''
        unchecked = ' selected="selected"'
    # Warning: the value of the "off" option is left intentionnaly
    # blank because Django seems to assume that any data (including "off") == True.
    return u"""<label for="%(id)s" class="ui-input-slider">%(label)s</label>\
<select name="%(name)s" id="%(id)s" data-role="slider">\
    <option value=""%(unchecked)s>%(off)s</option>\
    <option value="on"%(checked)s>%(on)s</option>\
</select>""" % {
        'id': field.field.auto_id, 
        'label': field.field.label, 
        'name': field.field.html_name,
        'on': _('On'),
        'off': _('Off'),
        'unchecked':  unchecked,
        'checked': checked
        }


def form_datetime(field):
    datetime=field.field
    #on place le titre
    out=u'<label for="%s"><h1>%s</h1></label>' % (datetime.auto_id,datetime.label)
    out+='<table>'
    
    html=datetime.as_widget()
    errors=(unicode(datetime.errors)).replace('<ul class="errorlist">','<span id="date_errors"><ul class="errorlist">').replace('</ul>','</ul></span>')
    
    #on recherche les sous titres
    exp=re.compile('([A-Z][a-z]*.:)')
    res_title=exp.findall(html)
    
    #on recherche les dates et heures corespondantes aux sous titres
    exp=re.compile('([0-9][0-9][:|/][0-9][0-9][:|/][0-9]*[0-9])')
    res_date_hour=exp.findall(html)
    
    #on cherche les classe corespondante au type de input (le premier trouvé est faux, car englobant)
    exp=re.compile('(class="[_A-Za-z0-9-]+")')
    _type=(exp.findall(html))
    #on met tout on place (sous titre + text )
    i=0
    for title in res_title:
        out+='<tr><td> <label for="%(id)s_%(i)d">%(label)s </label></td><td> <input type="text" %(_type)s value='% {'label':title,'id':datetime.auto_id,'i':i,'_type':_type[i+1] }
        if i < len(res_date_hour):
            out+='"%(value)s"' % {'value':res_date_hour[i]}
        elif "Time" in _type[i+1]:
            out+='"00:00:00"'
        else:
        	out+='"00/00/0000"'
        out+=' id="%(id)s_%(i)d" name="%(name)s_%(i)d"/> </td></tr>' % {'id':datetime.auto_id,'i':i, 'name': field.field.html_name }
        i+=1
    out+='</table>'
    out+= errors
    return out


@register.simple_tag
def render_mobile_field(field):
    html = field.field.as_widget()
    #html=html.replace('<a href="','<span id="button"><a href="').replace('</a>','</a></span>')
    #print (html+ '\n')
    
    
    
    if field.is_checkbox:
        out = form_flipswitch(field)
       #print "-------------------------------------------------------"
       #out = '%s <label for="%s" class="vCheckboxLabel" onclick="javascript:;">%s</label>' % (field.field, field.field.auto_id, field.field.label)1
       #print "-------------------------------------------------------"
    elif '<p class="datetime">' in html:
        out = form_datetime(field)
    else:
		#on récupère le possible bouton d'ajout
		exp=re.compile('(<a href=".*></a>$)');
		bottom_button=exp.findall(html);
		href='';		
		#print (html+'\n')
		#on regarde si il y a effectivement un bouton d'ajout
		if(len(bottom_button)>0):
			html=html.replace(bottom_button[0],'')
			exp=re.compile('(<a href=".*;">)');
			href=(exp.findall(bottom_button[0]));
			href[0]=href[0].replace('<a','<a data-role="button" data-icon="plus"');

		out = u'<label for="%(id)s">%(label)s</label> %(objet)s' % {'id':field.field.auto_id, 
        'label':field.field.label,
         'objet':html,
         }
         #on ajout le bouton sous le reste
		if (href!=''):
			out+='<span id="%(id)s_button" >%(ajout)s %(new)s </a></span>' % {'id':field.field.auto_id,'ajout':href[0], 'new':_("New")}
		elif '<input name="password"' in html:
			out+='<span id="%(id)s_button" ><a data-role="button" data-icon="gear" href="password" id="modif_mdp">%(label)s</a></span>' % {
                    'id':field.field.auto_id,
                    'label': _('Change Password'),
                    }
        
		out+='<span id="%(id)s_errors" >%(errors)s</span>' % {'id':field.field.auto_id,'errors':unicode(field.field.errors)}
		
		#inclure le fichier livevalidation_standalone.compressed.js pour des verification en temps réel
    	#if 'type="text"' in html:
        #	out+='<script type="text/javascript">'
        #	if "email" in html:
        #		out+='var %(id)s = new LiveValidation("%(id)s", { validMessage: "%(valid)s" ,wait: 500});\n %(id)s.add(Validate.Presence, {failureMessage: "%(fail)s" });\n %(id)s.add(Validate.Format, {pattern: /^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$/i,failureMessage: "%(fail)s" });' % {'id':field.field.auto_id,'valid':"email correct",'fail': "email incorrect"}        		
        #	out+='</script>'
    return out


@register.simple_tag
def get_breadcrumb(field,name=''):
	path = field
	exp = re.compile('([A-Z a-z 0-9]+/)')
	sub_path = exp.findall(path)
	out = u'<div data-role="navbar"><ul class="breadcrumbs">'
	i = 1;
	path = "/"
	last_sub = ''

	#on parcour l'arborecence
	for page in sub_path:
		path +=page #on reconstruit l'arborecence à chaque boucle
		out +='<li><a href="%(path)s"' % {'path':path} #on forme la liste des boutons
		
		if i == len(sub_path):
            # on active le dernier lien
			out +=' class="ui-btn-active"' 

		if i == len(sub_path) and name != '':
			page = unicode(name)
		
		if i == 1:
			out +=' class="ui-btn-home"><span class="hidden">%s</span><span class="home-icon">&nbsp;</span></a></li>' % _('Home')
		else:
			out +='>%(page)s</a></li>' % {'page': page.replace('/', '')} # on fini la liste
		i +=1	
		last_sub =page
	out+='</ul></div>'

	return out
	
@register.simple_tag
def get_back_path(field):
	path=field
	exp=re.compile('([A-Z a-z 0-9]+/)')
	sub_path=exp.findall(path)
	i=1;
	if i < len(sub_path):
		path="/"
		for page in sub_path:
			if i < len(sub_path):
				path+=page
			i+=1
	else:
		path="./"
	#on parcour l'arborecence
	
	return path