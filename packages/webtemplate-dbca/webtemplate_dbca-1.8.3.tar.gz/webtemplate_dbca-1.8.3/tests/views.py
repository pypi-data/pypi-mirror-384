from django.views.generic import TemplateView


class TestB4Page(TemplateView):
    template_name = "webtemplate_dbca/base_b4.html"

    def get_context_data(self, **kwargs):
        context = super(TestB4Page, self).get_context_data(**kwargs)
        context["page_title"] = "Test Bootstrap 4 page"
        context["page_description"] = "Meta tag page description"
        context["site_title"] = "SITE TITLE"
        return context


class TestB5Page(TemplateView):
    template_name = "webtemplate_dbca/base_b5.html"

    def get_context_data(self, **kwargs):
        context = super(TestB5Page, self).get_context_data(**kwargs)
        context["page_title"] = "Test Bootstrap 5 page"
        context["page_description"] = "Meta tag page description"
        context["site_title"] = "SITE TITLE"
        return context


class TestPage2(TestB5Page):
    template_name = "tests/test_page2.html"


class LoginView(TemplateView):
    template_name = "webtemplate_dbca/base_b5.html"

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context["page_title"] = "Test login page"
        context["site_title"] = "LOGIN"
        return context


class LogoutView(TemplateView):
    template_name = "webtemplate_dbca/base_b5.html"

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context["page_title"] = "Test logout page"
        context["site_title"] = "LOGOUT"
        return context
