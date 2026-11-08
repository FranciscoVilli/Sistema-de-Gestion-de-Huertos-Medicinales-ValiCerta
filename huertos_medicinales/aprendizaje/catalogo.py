"Reglas de avance educativo. No equivalen a certificación profesional."

XP_POR_LECCION = 25
NIVELES = ((0, "Aprendiz"), (75, "Oficial"), (150, "Maestro"))
PLANTAS = (
    {
        "slug": "manzanilla",
        "nombre": "Manzanilla",
        "nombre_cientifico": "Matricaria chamomilla",
        "xp": XP_POR_LECCION,
        "nota": "Tu primera ficha de aprendizaje.",
        "descripcion": (
            "Planta herbácea anual de la familia de las margaritas "
            "(Asteraceae), de flores pequeñas con pétalos blancos y "
            "centro amarillo."
        ),
        "cultivo": (
            "En términos generales prefiere un lugar con sol directo, "
            "aunque tolera algo de sombra. Se adapta a sustratos poco "
            "fértiles, pero crece mejor con riego regular que mantenga "
            "el sustrato húmedo sin encharcarlo. No suele trasplantarse "
            "bien una vez establecida, por lo que conviene sembrarla "
            "directamente en su recipiente definitivo."
        ),
        "fuente_nombre": "NC State Extension · Matricaria chamomilla",
        "fuente_url": (
            "https://plants.ces.ncsu.edu/plants/matricaria-chamomilla/"
            "common-name/chamomile/"
        ),
        "luz": "sol",
        "sustrato": "equilibrado",
        "ilustracion_flor": True,
        "ilustracion_hoja_rx": 16,
        "ilustracion_hoja_ry": 8,
        "dias_germinacion": 10,
        "dias_madurez": 60,
        "fuente_tiempos_nombre": "The Old Farmer's Almanac · Chamomile",
        "fuente_tiempos_url": "https://www.almanac.com/plant/chamomile",
    },
    {
        "slug": "menta",
        "nombre": "Menta",
        "nombre_cientifico": "Mentha spicata",
        "xp": 50,
        "nota": "Otra planta para ampliar tus preguntas y observaciones.",
        "descripcion": (
            "Planta herbácea perenne de la familia de las mentas "
            "(Lamiaceae), de hojas aromáticas y crecimiento expansivo "
            "por estolones."
        ),
        "cultivo": (
            "En términos generales tolera la sombra parcial y prefiere "
            "un sustrato rico en materia orgánica que se mantenga "
            "húmedo, ya que no se desarrolla bien en condiciones secas. "
            "Por su tendencia a expandirse con rapidez, suele cultivarse "
            "en un recipiente propio que limite sus raíces."
        ),
        "fuente_nombre": "NC State Extension · Mentha spicata",
        "fuente_url": "https://plants.ces.ncsu.edu/plants/mentha-spicata/",
        "luz": "sombra",
        "sustrato": "compacto",
        "ilustracion_flor": False,
        "ilustracion_hoja_rx": 18,
        "ilustracion_hoja_ry": 9,
        "dias_germinacion": 12,
        "dias_madurez": 49,
        "fuente_tiempos_nombre": "The Old Farmer's Almanac · Mint",
        "fuente_tiempos_url": "https://www.almanac.com/plant/mint",
    },
    {
        "slug": "calendula",
        "nombre": "Caléndula",
        "nombre_cientifico": "Calendula officinalis",
        "xp": 100,
        "nota": "Nuevas observaciones en tu camino de cultivo.",
        "descripcion": (
            "Planta herbácea anual de la familia de las margaritas "
            "(Asteraceae), de flores grandes en tonos amarillos y "
            "anaranjados."
        ),
        "cultivo": (
            "En términos generales prefiere sol pleno, aunque tolera "
            "sombra parcial en climas muy cálidos. Se adapta a distintos "
            "tipos de sustrato siempre que tengan buen drenaje. Retirar "
            "las flores marchitas favorece que la planta siga "
            "floreciendo."
        ),
        "fuente_nombre": "NC State Extension · Calendula officinalis",
        "fuente_url": "https://plants.ces.ncsu.edu/plants/calendula-officinalis/",
        "luz": "sol",
        "sustrato": "ligero",
        "ilustracion_flor": True,
        "ilustracion_hoja_rx": 16,
        "ilustracion_hoja_ry": 8,
        "dias_germinacion": 7,
        "dias_madurez": 52,
        "fuente_tiempos_nombre": "The Old Farmer's Almanac · Calendula",
        "fuente_tiempos_url": "https://www.almanac.com/plant/calendula",
    },
    {
        "slug": "romero",
        "nombre": "Romero",
        "nombre_cientifico": "Salvia rosmarinus",
        "xp": 150,
        "nota": "Una nueva ficha al completar esta ruta inicial.",
        "descripcion": (
            "Arbusto perenne y aromático de la familia de las mentas "
            "(Lamiaceae), de hojas pequeñas y alargadas."
        ),
        "cultivo": (
            "En términos generales necesita un lugar soleado y un "
            "sustrato con muy buen drenaje; tolera bien la sequía, pero "
            "no los ambientes húmedos o encharcados. Se propaga con "
            "facilidad por esqueje."
        ),
        "fuente_nombre": "NC State Extension · Salvia rosmarinus",
        "fuente_url": (
            "https://plants.ces.ncsu.edu/plants/salvia-rosmarinus/"
            "common-name/rosemary/"
        ),
        "luz": "sol",
        "sustrato": "ligero",
        "ilustracion_flor": False,
        "ilustracion_hoja_rx": 6,
        "ilustracion_hoja_ry": 16,
        "dias_germinacion": 20,
        "dias_madurez": 90,
        "fuente_tiempos_nombre": "The Old Farmer's Almanac · Rosemary",
        "fuente_tiempos_url": "https://www.almanac.com/plant/rosemary",
    },
)
LECCIONES = (
    {
        "slug": "conoce-tu-espacio",
        "titulo": "Conoce tu espacio",
        "tema": "LUZ Y OBSERVACIÓN",
        "texto": (
            (
                "Antes de elegir una planta, observa el lugar disponible. "
                "Anota cuándo recibe luz, cómo puedes acercarte a cuidarla "
                "y cuánto espacio tienes. La elección debe considerar las "
                "necesidades de cada especie y las condiciones del lugar."
            ),
            (
                "La luz cambia a lo largo del día: un lugar puede recibir "
                "sol directo por la mañana y sombra por la tarde, o al "
                "revés. Observa varios momentos del día antes de decidir, "
                "y fíjate también en el viento, el paso de personas o "
                "mascotas, y si puedes regar con comodidad sin afectar "
                "otras plantas cercanas."
            ),
        ),
        "practica": (
            "Mira el espacio donde te gustaría comenzar y anota qué "
            "observas. Esta pregunta comprueba el concepto; no "
            "certifica que ya realizaste una siembra."
        ),
        "pregunta": "¿Cuál es un buen primer paso para elegir dónde cultivar?",
        "opciones": (
            "Observar la luz y el espacio disponible.",
            "Elegir un lugar sin mirar sus condiciones.",
            "Suponer que todas las plantas necesitan lo mismo.",
        ),
        "correcta": "0",
        "explicacion": (
            "Conocer el lugar te ayuda a contrastar sus condiciones con"
            " la guía de la especie elegida."
        ),
    },
    {
        "slug": "elige-tu-recipiente",
        "titulo": "Elige tu recipiente",
        "tema": "PREPARA TU PRIMERA SIEMBRA",
        "texto": (
            (
                "Una maceta puede ser el comienzo de tu huerto. El tamaño, "
                "el sustrato y la salida del agua deben elegirse de acuerdo"
                " con la especie y su guía de cultivo. Un recipiente bonito"
                " no siempre es el adecuado para sus necesidades."
            ),
            (
                "Un recipiente sin orificios de drenaje puede acumular "
                "agua y afectar la raíz, incluso si el sustrato parece "
                "adecuado. El material también influye: los recipientes "
                "porosos, como el barro, pierden humedad más rápido que "
                "los de plástico. Ninguna de estas decisiones reemplaza "
                "la guía específica de la especie que elijas."
            ),
        ),
        "practica": (
            "Observa un recipiente que tengas y escribe qué "
            "necesitarías comprobar antes de usarlo."
        ),
        "pregunta": "¿Qué debería orientar la elección del recipiente?",
        "opciones": (
            "Solo su color.",
            "Las necesidades de la especie y el manejo del agua.",
            "Que sea siempre el más pequeño.",
        ),
        "correcta": "1",
        "explicacion": (
            "Las condiciones de cultivo importan más que el aspecto del recipiente."
        ),
    },
    {
        "slug": "siembra-con-una-guia",
        "titulo": "Siembra con una guía",
        "tema": "DEL CONOCIMIENTO A LA PRÁCTICA",
        "texto": (
            (
                "No todas las plantas se propagan de la misma manera. Antes"
                " de sembrar, consulta instrucciones revisadas para la "
                "especie, el método de propagación y las condiciones del "
                "lugar. Una guía general no reemplaza los pasos específicos"
                " de cada planta."
            ),
            (
                "Algunas plantas se propagan por semilla, otras por "
                "esqueje o división, y los tiempos de germinación varían "
                "ampliamente entre especies. Si encuentras información "
                "contradictoria entre fuentes, prioriza materiales de "
                "instituciones educativas o de extensión agrícola antes "
                "que publicaciones sin autoría clara."
            ),
        ),
        "practica": (
            "Elige qué te gustaría cultivar y busca qué información "
            "necesitarías para iniciar su siembra. Las fichas de esta "
            "versión aún no incluyen instrucciones específicas "
            "revisadas."
        ),
        "pregunta": "Antes de sembrar una planta que no conoces, ¿qué conviene hacer?",
        "opciones": (
            "Copiar sin cambios lo que se hizo con otra especie.",
            "Adivinar el método de propagación.",
            "Consultar una guía revisada para esa especie y contexto.",
        ),
        "correcta": "2",
        "explicacion": "Cada especie y contexto pueden requerir decisiones diferentes.",
    },
    {
        "slug": "observa-antes-de-regar",
        "titulo": "Observa antes de regar",
        "tema": "AGUA Y CUIDADOS",
        "texto": (
            (
                "El cuidado requiere observar. Antes de decidir sobre el "
                "riego, revisa las condiciones del sustrato y las "
                "indicaciones de la especie. En esta ruta no proponemos una"
                " frecuencia universal de riego para todas las plantas."
            ),
            (
                "Una forma sencilla de observar es introducir un dedo "
                "unos centímetros en el sustrato: si se siente húmedo, "
                "probablemente no necesita agua todavía. Regar en exceso "
                "puede ser tan perjudicial como no regar lo suficiente, "
                "porque dificulta que la raíz respire. Registra estos "
                "efectos en Mis prácticas cuando siembres de verdad."
            ),
        ),
        "practica": (
            "Anota qué información consultarías antes de decidir si una"
            " planta necesita agua."
        ),
        "pregunta": "¿Cómo tomar una decisión informada sobre el riego?",
        "opciones": (
            "Observar el sustrato y consultar la guía de la especie.",
            "Regar siempre, sin observar.",
            "Usar una única frecuencia para todas las plantas.",
        ),
        "correcta": "0",
        "explicacion": (
            "La observación y la guía ayudan a adaptar el cuidado a cada caso."
        ),
    },
    {
        "slug": "conoce-tu-suelo",
        "titulo": "Conoce tu suelo",
        "tema": "SUELO Y ABONOS",
        "texto": (
            (
                "El suelo o sustrato forma parte del entorno de la planta. "
                "Antes de añadir abonos, conviene conocer sus "
                "características y revisar las necesidades de la especie. "
                "Más abono no significa automáticamente mejor cuidado."
            ),
            (
                "La textura del sustrato influye en cuánta agua retiene: "
                "uno más compacto retiene más humedad, mientras uno más "
                "ligero drena más rápido. Revisa la ficha de tu planta "
                "para conocer el sustrato que prefiere antes de decidir "
                "qué usar en tu siembra real."
            ),
        ),
        "practica": (
            "Describe lo que sabes del suelo o sustrato de tu espacio y"
            " qué información aún te falta."
        ),
        "pregunta": "¿Qué conviene hacer antes de añadir un abono?",
        "opciones": (
            "Añadir la mayor cantidad posible.",
            "Conocer el sustrato y revisar las necesidades del cultivo.",
            "Elegirlo únicamente por el empaque.",
        ),
        "correcta": "1",
        "explicacion": (
            "Una decisión sobre abonos debe partir del contexto y las "
            "necesidades del cultivo."
        ),
    },
    {
        "slug": "registra-y-aprende",
        "titulo": "Registra y aprende",
        "tema": "TU EXPERIENCIA CUENTA",
        "texto": (
            (
                "La bitácora ayuda a relacionar lo que haces con lo que "
                "observas. Registra fechas, acciones, cambios y "
                "dificultades. Un resultado distinto al esperado también "
                "puede generar preguntas y aprendizaje."
            ),
            (
                "Una bitácora útil no es solo una lista de tareas: "
                "incluye lo que esperabas que pasara y lo que realmente "
                "ocurrió. Con el tiempo, comparar varias observaciones te "
                "ayuda a notar patrones que una sola entrada no muestra, "
                "como qué condiciones se repiten antes de un cambio en "
                "la planta."
            ),
        ),
        "practica": (
            "Escribe una observación breve. En Mis prácticas "
            "puedes registrar una siembra y añadir observaciones. Tu "
            "bitácora se guarda en tu cuenta."
        ),
        "pregunta": "¿Qué registro aporta más al aprendizaje?",
        "opciones": (
            "Escribir solo cuando todo sale bien.",
            "Ocultar las dificultades.",
            "Anotar fechas, acciones y resultados, incluidos los intentos.",
        ),
        "correcta": "2",
        "explicacion": (
            "Una bitácora útil conserva tanto cambios como dificultades y decisiones."
        ),
    },
)
