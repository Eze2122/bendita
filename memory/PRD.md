# Bendita Accesorios — PRD

## Problema original
Crear desde cero una tienda online profesional para Bendita Accesorios usando el logo y sublogo oficiales, sin inventar productos, precios, stock ni promociones. La tienda debe ser editorial, responsive, preparada para crecer y contar con una administración sencilla de productos y categorías sin editar código.

## Decisiones de arquitectura
- Frontend React con React Router, Axios y CSS editorial responsive.
- Backend FastAPI con MongoDB mediante Motor; los documentos exponen IDs string y excluyen `_id`.
- Catálogo persistente con productos, categorías y borrado lógico de productos.
- Carga de imágenes mediante almacenamiento de objetos administrado; MongoDB conserva la referencia canónica.
- La ruta `/admin` permite administrar el catálogo sin modificar código. No se añadió autenticación porque no fue solicitada.

## Implementado
- Home Bendita completamente nueva con logos oficiales, hero editorial, categorías, filtros, sección de marca, espacios sociales preparados y footer.
- Estados vacíos con imágenes de inspiración claramente marcadas como “Próximamente”, sin precios ni datos comerciales inventados.
- Bolsa lateral funcional con estado vacío, cantidades, eliminación y estructura de total preparada.
- API CRUD de productos y categorías, con campos para nombre, descripción, precio opcional, categoría, audiencia, stock, galería, variantes y flags Nuevo/Destacado/Oferta.
- Panel de administración con crear, editar, eliminar, carga de imágenes, vista previa y alta de categorías.
- Validaciones de sintaxis, lint y pruebas funcionales frontend/backend completadas.
- Ajuste visual solicitado: H1 en `#A782DA`, extraído del lila del logo oficial, H2 en negro, sin cambios en fondos, estructura, botones ni animaciones.
- Logos oficiales convertidos a PNG RGBA transparente y usados directamente desde `/bendita-logo-transparent.png` y `/bendita-sublogo-transparent.png`.
- Ajuste posterior: el segundo logo ahora reutiliza el PNG transparente correcto del banner y todos los textos marrones fueron convertidos a negro; la comprobación visual detectó cero textos marrones.
- Ajuste posterior: toda la interfaz usa fondo blanco, manteniendo las fotografías editoriales; el segundo logo se muestra directamente sobre blanco con transparencia real y la comprobación confirmó cero textos marrones.
- Ajuste posterior: la imagen editorial compartida por las áreas “Hombre” ahora muestra claramente a un hombre con estilo masculino; la imagen de “Mujer” se mantuvo intacta.
- Ajuste posterior: el nuevo archivo `Bendita-2-mda-logo-01.webp` se usa únicamente como logo principal grande del banner (400×400, proporción conservada); el logo superior y los dos lugares del sublogo permanecen sin cambios.
- Ajuste posterior: el encabezado ahora usa el último archivo oficial `Bendita-2-mda-logo-01.webp` con tamaño contenido de 130px de ancho; el logo grande del banner y los dos sublogos permanecen sin cambios.

## Backlog priorizado
- P0: Añadir autenticación y permisos para proteger `/admin` antes de publicar el catálogo real.
- P1: Incorporar detalle de producto, checkout y método de pago cuando existan productos reales.
- P1: Añadir configuración editable de Instagram, WhatsApp y otros enlaces desde el panel.
- P2: Añadir variantes estructuradas y filtros avanzados de catálogo.