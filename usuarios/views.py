from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.messages import constants
from django.contrib import auth

# Create your views here.
def cadastro(request):   
    if request.method == "GET":
        return render(request, 'cadastro.html')
    elif request.method == "POST":       
        username = request.POST.get('username')        
        senha = request.POST.get('senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if senha != confirmar_senha:
            messages.add_message(request, constants.ERROR, 'As senhas não coincidem')
            return redirect('/usuarios/cadastro')
        
        if len(senha) < 6:
            messages.add_message(request, constants.ERROR, 'A senha precisa ter ao menos 6 caracteres')
            return redirect('/usuarios/cadastro')

        # pesquisa se já existe username cadastrado
        user = User.objects.filter(username=username)

        if user.exists():
            messages.add_message(request, constants.ERROR, 'Nome de usuário já existe')
            return redirect('/usuarios/cadastro')

        user = User.objects.create_user(
            username=username,
            password=senha
        )

        user.save()

        messages.add_message(request, constants.SUCCESS, 'Usuário foi cadastrado')
        return redirect('/usuarios/logar')
    
def logar(request):
    if request.method == "GET":
        return render(request, 'logar.html')
    elif request.method == "POST":
        username = request.POST.get('username')
        senha = request.POST.get('senha')

        user = auth.authenticate(request, username=username, password=senha)

        if user:
            auth.login(request, user)
            return redirect('/empresarios/cadastrar_empresa')

        messages.add_message(request, constants.ERROR, 'Usuario ou senha inválidos')
        return redirect('/usuarios/logar')