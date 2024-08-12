from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.contrib.messages import constants
from empresarios.models import Empresas, Documento, Metricas
from .models import PropostaInvestimento
from django.db.models import Q

@login_required
def sugestao(request):
    areas = Empresas.area_choices
    if request.method == "GET":   
        return render(request, 'sugestao.html', {'areas': areas})
    elif request.method == "POST":
        tipo = request.POST.get('tipo')
        area = request.POST.getlist('area')
        valor = request.POST.get('valor')

        if tipo == 'C':
            empresas = Empresas.objects.filter(tempo_existencia='+5').filter(estagio="E")
        elif tipo == 'D':
            empresas = Empresas.objects.filter(tempo_existencia__in=['-6', '+6', '+1']).exclude(estagio="E")
        elif tipo == 'I':
            empresas = Empresas.objects.filter(
                ~(Q(tempo_existencia='+5') & Q(estagio="E")) &
                ~(Q(tempo_existencia__in=['-6', '+6', '+1']) & ~Q(estagio="E"))
            )
        
        empresas = empresas.filter(area__in=area)
        
        empresas_selecionadas = []
        for empresa in empresas:
            percentual = (float(valor) * 100) / float(empresa.valuation)
            if percentual >= 1:
                empresas_selecionadas.append(empresa)
        print(empresas_selecionadas)
        return render(request, 'sugestao.html', {'empresas_selecionadas': empresas_selecionadas, 'areas': areas})

@login_required
def ver_empresa(request, id):
    empresa = Empresas.objects.get(id=id)
    documentos = Documento.objects.filter(empresa=empresa)
    metricas = Metricas.objects.filter(empresa=empresa)
    proposta_investimentos = PropostaInvestimento.objects.filter(empresa=empresa)

    percentual_vendido = sum(proposta_investimentos.filter(status='PA').values_list('percentual', flat=True))

    limiar = (80 * empresa.percentual_equity) / 100

    concretizado = percentual_vendido >= limiar      

    percentual_disponivel = empresa.percentual_equity - percentual_vendido

    return render(request, 'ver_empresa.html', {'empresa': empresa, 
                                                'documentos': documentos, 
                                                'metricas': metricas,
                                                'percentual_vendido': int(percentual_vendido),
                                                'concretizado': concretizado,
                                                'percentual_disponivel': percentual_disponivel})

@login_required
def realizar_proposta(request, id):
    valor = request.POST.get('valor')
    percentual = request.POST.get('percentual')
    empresa = Empresas.objects.get(id=id)

    propostas_aceitas = PropostaInvestimento.objects.filter(empresa=empresa).filter(status='PA')
    
    total = 0
    for pa in propostas_aceitas:
        total = total + pa.percentual

    if total + int(percentual)  > empresa.percentual_equity:
        messages.add_message(request, constants.WARNING, 'O percentual solicitado ultrapassa o percentual máximo.')
        return redirect(f'/investidores/ver_empresa/{id}')

    valuation = (100 * int(valor)) / int(percentual)

    if valuation < (int(empresa.valuation) / 2):
        messages.add_message(request, constants.WARNING, f'Seu valuation proposto foi R$ {valuation} e deve ser no mínimo R$ {empresa.valuation/2}')
        return redirect(f'/investidores/ver_empresa/{id}')

    pi = PropostaInvestimento(
        valor = valor,
        percentual = percentual,
        empresa = empresa,
        investidor = request.user,
    )

    pi.save()

    #messages.add_message(request, constants.SUCCESS, f'Proposta enviada com sucesso')
    return redirect(f'/investidores/assinar_contrato/{pi.id}')

@login_required
def assinar_contrato(request, id):
    pi = PropostaInvestimento.objects.get(id=id)
    if pi.status != "AS":
        raise Http404()
    
    if request.method == "GET":
        return render(request, 'assinar_contrato.html', {'pi': pi})
    elif request.method == "POST":
        selfie = request.FILES.get('selfie')
        rg = request.FILES.get('rg')      

        pi.selfie = selfie
        pi.rg = rg
        pi.status = 'PE'
        pi.save()

        messages.add_message(request, constants.SUCCESS, f'Contrato assinado com sucesso, sua proposta foi enviada a empresa.')
        return redirect(f'/investidores/ver_empresa/{pi.empresa.id}')
