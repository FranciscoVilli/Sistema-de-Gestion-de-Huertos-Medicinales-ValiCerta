"""Resúmenes educativos por especie. Fuentes consultadas el 2026-11-06."""

FICHAS_MEDICINALES = {'manzanilla': {'parte': 'Flores',
                'evidencia': 'Evidencia clínica limitada',
                'formas': 'Infusión y preparados tópicos',
                'resumen': 'Se utiliza tradicionalmente para molestias digestivas y para favorecer '
                           'el descanso. La evidencia clínica aún no permite asegurar su eficacia '
                           'para estas indicaciones.',
                'tarjetas': [('Digestión',
                              'Uso tradicional',
                              'Se usa para malestar digestivo; los estudios con mezclas no prueban '
                              'el efecto de la manzanilla sola.'),
                             ('Ansiedad',
                              'Investigación preliminar',
                              'Algunos ensayos con suplementos sugieren posibles beneficios; no '
                              'equivalen a demostrar el efecto de una infusión.'),
                             ('Sueño',
                              'Evidencia insuficiente',
                              'No está demostrada como tratamiento del insomnio.'),
                             ('Boca y piel',
                              'Preparaciones específicas',
                              'Se han estudiado enjuagues y productos tópicos; los resultados no '
                              'se trasladan a cualquier preparación casera.')],
                'uso': 'Las flores se emplean en bebidas y en preparados de composición definida.',
                'precaucion': 'Puede causar alergia, especialmente en personas sensibles a las '
                              'margaritas y otras Asteraceae. Puede interactuar con warfarina y '
                              'otros medicamentos. La seguridad durante embarazo y lactancia no '
                              'está bien establecida.',
                'fuentes': [('NCCIH · Manzanilla', 'https://www.nccih.nih.gov/health/chamomile')]},
 'menta': {'parte': 'Hojas',
           'evidencia': 'Uso tradicional; estudios limitados',
           'formas': 'Infusión y extractos estudiados',
           'resumen': 'La Mentha spicata se usa tradicionalmente para molestias digestivas. Hay '
                      'investigaciones sobre sus extractos, pero no suficiente evidencia para '
                      'presentarla como un tratamiento eficaz.',
           'tarjetas': [('Molestias digestivas',
                         'Uso tradicional',
                         'Se ha utilizado para gases e indigestión; su beneficio clínico no está '
                         'bien demostrado.'),
                        ('Náuseas',
                         'Evidencia limitada',
                         'Los usos descritos y estudios con mezclas no prueban que una infusión de '
                         'esta especie las trate.'),
                        ('Actividad antimicrobiana',
                         'Estudios de laboratorio',
                         'Los resultados en laboratorio no demuestran que cure infecciones en '
                         'personas.'),
                        ('Identidad de la especie',
                         'Mentha spicata',
                         'Esta ficha corresponde a hierbabuena o menta verde. Los resultados sobre '
                         'Mentha × piperita no se pueden atribuir automáticamente a esta planta.')],
           'uso': 'Las hojas se usan como aromatizante y en infusiones. Los extractos y aceites no '
                  'equivalen a una bebida de hojas.',
           'precaucion': 'Antes de un uso medicinal, consulta si estás embarazada, amamantando, '
                         'tomas medicamentos o tienes enfermedad renal o hepática. Evita emplear '
                         'grandes cantidades como remedio.',
           'fuentes': [('El Menyiy y colaboradores · Revisión de Mentha spicata (2022)',
                        'https://pmc.ncbi.nlm.nih.gov/articles/PMC9019422/'),
                       ('MedlinePlus · Spearmint',
                        'https://medlineplus.awsqa.nlm.nih.gov/druginfo/natural/845.html')]},
 'calendula': {'parte': 'Flores',
               'evidencia': 'Uso tradicional reconocido por EMA',
               'formas': 'Preparados cutáneos y oromucosales',
               'resumen': 'Los preparados de flor de caléndula tienen usos tradicionales para '
                          'pequeñas inflamaciones de la piel, heridas menores y molestias '
                          'inflamatorias de boca o garganta. No son beneficios confirmados por '
                          'ensayos clínicos sólidos.',
               'tarjetas': [('Piel irritada',
                             'Uso tradicional',
                             'Preparados destinados a aliviar inflamaciones cutáneas leves.'),
                            ('Heridas menores',
                             'Uso tradicional',
                             'Empleo como ayuda en la cicatrización de heridas pequeñas; no para '
                             'lesiones profundas o infectadas.'),
                            ('Boca y garganta',
                             'Uso tradicional',
                             'Preparados oromucosales para inflamación leve, siguiendo las '
                             'indicaciones del producto.'),
                            ('Alcance de la evidencia',
                             'Ensayos insuficientes',
                             'La EMA basa estos usos en la experiencia tradicional; los estudios '
                             'disponibles no permiten conclusiones clínicas firmes.')],
               'uso': 'Se utilizan preparados para la piel o para contacto con la mucosa oral. No '
                      'son intercambiables con una receta casera.',
               'precaucion': 'No usar si existe alergia a las Asteraceae. Puede producir '
                             'sensibilización cutánea. Para productos medicinales, sigue el '
                             'prospecto y consulta al profesional sanitario.',
               'fuentes': [('EMA · Flor de caléndula',
                            'https://www.ema.europa.eu/en/medicines/herbal/calendulae-flos')]},
 'romero': {'parte': 'Hojas',
            'evidencia': 'Uso tradicional reconocido por EMA',
            'formas': 'Preparados de hojas y aditivos de baño',
            'resumen': 'Las hojas de romero se emplean tradicionalmente para indigestión y '
                       'espasmos digestivos leves. También existen preparados de baño para '
                       'molestias musculares o articulares menores.',
            'tarjetas': [('Indigestión',
                          'Uso tradicional',
                          'Preparados de hojas para el alivio sintomático de molestias digestivas '
                          'leves.'),
                         ('Espasmos digestivos',
                          'Uso tradicional',
                          'Uso descrito para espasmos gastrointestinales leves.'),
                         ('Músculos y articulaciones',
                          'Uso externo tradicional',
                          'Preparados como aditivo de baño para molestias menores.'),
                         ('Alcance de la evidencia',
                          'Ensayos insuficientes',
                          'La valoración de EMA se apoya en el uso prolongado, no en eficacia '
                          'demostrada mediante ensayos clínicos.')],
            'uso': 'La ficha se refiere a preparados medicinales de hojas; no autoriza ingerir '
                   'aceite esencial.',
            'precaucion': 'Los preparados medicinales de hojas no se recomiendan en menores de 12 '
                          'años, embarazo o lactancia, ni ante obstrucción biliar, cálculos, '
                          'inflamación de vesícula o enfermedad hepática. No aplicar sobre piel '
                          'lesionada o irritada.',
            'fuentes': [('EMA · Hoja de romero',
                         'https://www.ema.europa.eu/en/medicines/herbal/rosmarini-folium')]}}
