class AlunoSSOMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        aluno = request.session.get("aluno_sso")
        if aluno:
            request.aluno = aluno
            nome_completo = aluno.get("nome", "")
            request.primeiro_nome = nome_completo.split(" ")[0] if nome_completo else "Aluno"
        else:
            request.aluno = None
            request.primeiro_nome = None

        response = self.get_response(request)
        return response