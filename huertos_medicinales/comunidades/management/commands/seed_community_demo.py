from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from huertos_medicinales.comunidades.models import PerfilComunitario,JardinCompartido,Pregunta,Respuesta
from huertos_medicinales.comunidades.community_forms import fingerprint
from huertos_medicinales.seguimiento.models import Jardin,Practica

class Command(BaseCommand):
    help='Carga datos ficticios [DEMO] de comunidad en desarrollo, sin duplicarlos.'
    @transaction.atomic
    def handle(self,*args,**kwargs):
        if not settings.DEBUG: raise CommandError('Este comando solo se permite en desarrollo (DEBUG).')
        group,_=Group.objects.get_or_create(name='Huertos · Comunidad de demostración')
        now=timezone.now();today=timezone.localdate()
        rows=[('Ana','Ibarra',0.35,-78.12,'intermedio',['menta','manzanilla']),('Luis','Ibarra',0.33,-78.11,'inicial',['romero','menta']),('Rosa','Ibarra',0.36,-78.13,'intermedio',['calendula','manzanilla']),('Diego','Quito',-0.18,-78.47,'avanzado',['romero','calendula']),('Carmen','Quito',-0.20,-78.49,'inicial',['menta','calendula']),('Elena','Cuenca',-2.90,-79.00,'intermedio',['manzanilla','romero'])]
        people=[]
        for i,(name,city,lat,lon,level,plants) in enumerate(rows):
            u,created=get_user_model().objects.get_or_create(email=f'comunidad-demo-{i+1}@example.invalid',defaults={'name':'[DEMO] '+name,'is_active':True})
            if created:u.set_unusable_password();u.save(update_fields=['password'])
            u.groups.add(group);people.append(u)
            PerfilComunitario.objects.get_or_create(usuario=u,defaults={'nombre':'[DEMO] '+name,'nivel':level,'visible':True,'localidad':city,'experiencia':'Perfil ficticio de demostración para probar el foro y el mapa. El nivel y las conversaciones son ejemplos; no representan a una persona real.'})
            garden,_=Jardin.objects.get_or_create(propietario=u,nombre='[DEMO] Jardín de '+name)
            JardinCompartido.objects.get_or_create(jardin=garden,defaults={'visible':True,'localidad':city+' · Sector de demostración','latitud':lat,'longitud':lon})
            for slot,plant in enumerate(plants,1):
                Practica.objects.get_or_create(jardin=garden,posicion=slot,defaults={'participante':u,'titulo':'[DEMO] '+plant.capitalize(),'planta':plant,'inicio':today-timedelta(days=12+i*7+slot*3),'espacio':'[DEMO] Maceta de ejemplo','objetivo':'Datos ficticios para visualizar la comunidad; no corresponden a una siembra real.'})
        topics=[
          (0,'plagas','¿Cómo registrar manchas en las hojas de manzanilla?','He notado unas manchas y quiero aprender a documentarlas antes de sacar conclusiones. ¿Qué fotos y observaciones añadirían a la bitácora?',[
            'Yo fotografiaría la planta completa y el detalle de ambos lados de la hoja para comparar los cambios.',
            'También puedes anotar cuándo aparecieron y si cambiaron el riego o la ubicación. Una foto sola no confirma la causa.',
            'Gracias, voy a registrar esos detalles y consultar la guía antes de aplicar cualquier producto.']),
          (1,'riego','¿Cómo organizan el riego de la menta en maceta?','Estoy aprendiendo a observar el sustrato. ¿Ustedes registran la revisión de humedad aunque ese día no rieguen?',[
            'Sí, en mi registro distingo entre revisar el sustrato y regar; son actividades diferentes.',
            'Me sirve anotar si la maceta está bajo techo o expuesta a la lluvia. El clima exterior no describe por completo el interior.',
            'Me gusta esa idea. Voy a dejar registrada la observación aunque no añada agua.']),
          (2,'cultivo','¿Cómo comparar dos espacios para la caléndula?','Tengo una ventana y un patio. Quiero registrar las horas de luz y comparar el espacio antes de decidir dónde colocar la planta.',[
            'Podrías llevar un registro de la luz que recibe cada lugar durante varios días y contrastarlo con la ficha de la especie.',
            'Yo añadiría fotos tomadas desde el mismo lugar, indicando la hora y si estaba nublado.',
            'Gracias. Empezaré por observar los dos espacios antes de cambiar mi maceta.']),
          (3,'suelo','¿Qué datos anotan al preparar el sustrato?','Quiero que mi bitácora sea más clara. ¿Qué información dejan registrada sobre el recipiente y la mezcla utilizada?',[
            'Anotaría los materiales utilizados y la fecha de preparación para poder recordar exactamente qué cambió.',
            'También dejaría una foto del recipiente y de sus orificios de drenaje.',
            'Voy a agregar esos datos a mi primera observación.']),
          (4,'experiencias','Mi primera semana registrando el huerto','Lo que más me está ayudando es anotar una pequeña observación cada día. ¿Qué cambios les resultó más sencillo reconocer al empezar?',[
            'A mí me ayuda comparar fotos del mismo ángulo, en vez de confiar solo en la memoria.',
            'Yo cuento las hojas nuevas y anoto lo que realmente veo, aunque no haya cambios grandes.',
            'Qué buena idea: voy a usar el mismo punto para las fotos de esta semana.']),
          (5,'cosecha','¿Cómo preparar el registro de una futura cosecha?','Todavía estoy aprendiendo. Quiero saber qué información debería dejar en mi registro cuando llegue ese momento, siguiendo la guía de mi planta.',[
            'Puedes preparar campos para fecha, parte recolectada, cantidad y una fotografía.',
            'Revisaría primero la guía específica de la especie. El momento apropiado no se determina solo por los días transcurridos.',
            'Gracias. Dejaré la actividad planificada y confirmaré el estado real de la planta antes de realizarla.']),
          (0,'experiencias','¿Cómo nombran sus jardines para identificarlos?','Ahora tengo más de un espacio en la aplicación y quiero distinguir las macetas de la ventana de las del patio.',[
            'Un nombre como Ventana de la sala o Patio cubierto puede ayudarte sin publicar una dirección.',
            'Yo comparto solamente el sector general cuando muestro mi jardín en la comunidad.',
            'Perfecto, usaré nombres por espacio y revisaré la privacidad antes de compartir.']),
          (1,'riego','¿Cómo usan el pronóstico del calendario?','Veo probabilidad de lluvia, pero mi planta está en un balcón cubierto. ¿Cómo lo registrarían en la planificación?',[
            'Marcaría que el espacio está cubierto para que el consejo de clima tenga ese contexto.',
            'En la actividad anotaría revisar la humedad; que llueva fuera no significa que el agua alcance la maceta.',
            'Entendido. Separaré el pronóstico de lo que observo realmente en el sustrato.'])]
        for i,(owner,category,title,body,replies) in enumerate(topics):
            title='[DEMO] '+title;body='[DEMO · Conversación ficticia de ejemplo]\n\n'+body
            q,created=Pregunta.objects.get_or_create(autor=people[owner],huella=fingerprint(title,body),oculta=False,defaults={'titulo':title,'contenido':body,'categoria':category,'resuelta':i in (1,6)})
            if created:Pregunta.objects.filter(pk=q.pk).update(creada=now-timedelta(hours=3+i*9),actualizada=now-timedelta(hours=2+i*9))
            for j,text in enumerate(replies):
                author=people[owner] if j==2 else people[(owner+j+1)%len(people)]
                text='[DEMO] '+text
                answer,created=Respuesta.objects.get_or_create(pregunta=q,autor=author,huella=fingerprint(text),oculta=False,defaults={'contenido':text})
                if created:Respuesta.objects.filter(pk=answer.pk).update(creada=now-timedelta(hours=2+i*9,minutes=30-j*10))
        self.stdout.write(self.style.SUCCESS('Comunidad DEMO: 6 perfiles, 6 jardines, 12 cultivos, 8 preguntas y 24 respuestas. Sin cambios en tus cultivos.'))
