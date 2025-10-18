from rest_framework import routers

from w.tests.fixtures.datasets.django_app.viewsets import SimpleViewset, ModelViewset

router = routers.SimpleRouter()
router.register(r"simples", SimpleViewset, basename="simple")
router.register(r"models", ModelViewset, basename="model")
urlpatterns = router.urls
