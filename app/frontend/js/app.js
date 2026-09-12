// =========================================================
// CONFIGURAÇÃO
// =========================================================

// Durante os testes locais, utilizaremos o FastAPI local.
//
// Quando o backend estiver publicado no Google Cloud Run,
// alteraremos somente esta constante.
//
// Exemplo futuro:
//
// const API_URL = "https://seu-backend-xxxxx.run.app";
//
const API_URL = "http://127.0.0.1:8000";


// =========================================================
// ELEMENTOS DA PÁGINA
// =========================================================

const formFatura = document.getElementById("form-fatura");
const arquivoInput = document.getElementById("arquivo");
const btnAnalisar = document.getElementById("btn-analisar");
const mensagem = document.getElementById("mensagem");

const resultado = document.getElementById("resultado");

const referencia = document.getElementById("referencia");
const consumo = document.getElementById("consumo");
const bandeira = document.getElementById("bandeira");

const totalCemig = document.getElementById("total-cemig");
const totalSemGd = document.getElementById("total-sem-gd");

const valorEmpresa = document.getElementById("valor-empresa");

const resumoCemig = document.getElementById("resumo-cemig");
const resumoEmpresa = document.getElementById("resumo-empresa");
const custoTotal = document.getElementById("custo-total");

const economia = document.getElementById("economia");
const percentual = document.getElementById("percentual");


// =========================================================
// ESTADO
// =========================================================

let dadosFatura = null;


// =========================================================
// FORMATAÇÃO DE MOEDA
// =========================================================

function formatarMoeda(valor) {

    return Number(valor).toLocaleString(
        "pt-BR",
        {
            style: "currency",
            currency: "BRL"
        }
    );
}


// =========================================================
// CONVERSÃO DO VALOR DIGITADO
// =========================================================

function converterValor(valor) {

    if (!valor) {
        return 0;
    }

    let texto = valor
        .trim()
        .replace(/\s/g, "");

    // Formato brasileiro:
    // 1.234,56
    if (
        texto.includes(",")
        && texto.includes(".")
    ) {
        texto = texto
            .replace(/\./g, "")
            .replace(",", ".");
    }

    // Formato:
    // 209,09
    else if (texto.includes(",")) {
        texto = texto.replace(",", ".");
    }

    const numero = Number(texto);

    return Number.isFinite(numero)
        ? numero
        : 0;
}


// =========================================================
// EXIBIÇÃO DE MENSAGEM
// =========================================================

function mostrarMensagem(
    texto,
    tipo = "info"
) {

    mensagem.className = `alert alert-${tipo} mt-3`;
    mensagem.textContent = texto;
}


// =========================================================
// LIMPAR MENSAGEM
// =========================================================

function limparMensagem() {

    mensagem.className = "";
    mensagem.textContent = "";
}


// =========================================================
// ENVIO DA FATURA
// =========================================================

formFatura.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        limparMensagem();

        const arquivo = arquivoInput.files[0];

        if (!arquivo) {

            mostrarMensagem(
                "Selecione um arquivo PDF.",
                "warning"
            );

            return;
        }


        if (
            arquivo.type !== "application/pdf"
            && !arquivo.name.toLowerCase().endsWith(".pdf")
        ) {

            mostrarMensagem(
                "O arquivo deve ser um PDF.",
                "warning"
            );

            return;
        }


        const formData = new FormData();

        formData.append(
            "arquivo",
            arquivo
        );


        btnAnalisar.disabled = true;
        btnAnalisar.textContent = "Processando...";


        try {

            const response = await fetch(
                `${API_URL}/faturas/ler`,
                {
                    method: "POST",
                    body: formData
                }
            );


            if (!response.ok) {

                let detalhe =
                    "Não foi possível processar a fatura.";

                try {

                    const erro = await response.json();

                    if (erro.detail) {
                        detalhe = erro.detail;
                    }

                } catch {
                    // Mantém mensagem padrão.
                }

                throw new Error(detalhe);
            }


            dadosFatura = await response.json();

            exibirFatura(
                dadosFatura
            );

            mostrarMensagem(
                "Fatura processada com sucesso.",
                "success"
            );

        } catch (error) {

            console.error(error);

            mostrarMensagem(
                error.message,
                "danger"
            );

        } finally {

            btnAnalisar.disabled = false;
            btnAnalisar.textContent = "Analisar fatura";
        }

    }
);


// =========================================================
// EXIBIR DADOS DA FATURA
// =========================================================

function exibirFatura(fatura) {

    referencia.textContent =
        fatura.referencia ?? "-";


    consumo.textContent =
        fatura.consumo_kwh != null
            ? `${fatura.consumo_kwh} kWh`
            : "-";


    bandeira.textContent =
        fatura.bandeira ?? "-";


    totalCemig.textContent =
        formatarMoeda(
            fatura.total
        );


    totalSemGd.textContent =
        formatarMoeda(
            fatura.total_sem_gd
            ?? fatura.total_sem_credito_cemig
            ?? 0
        );


    resumoCemig.textContent =
        formatarMoeda(
            fatura.total
        );


    atualizarCalculo();


    resultado.classList.remove(
        "d-none"
    );
}


// =========================================================
// ATUALIZAÇÃO DO CÁLCULO
// =========================================================

function atualizarCalculo() {

    if (!dadosFatura) {
        return;
    }


    const totalDistribuidora =
        Number(dadosFatura.total);


    const totalSemGeracao =
        Number(
            dadosFatura.total_sem_gd
            ?? dadosFatura.total_sem_gd
            ?? 0
        );


    const valorDaEmpresa =
        converterValor(
            valorEmpresa.value
        );


    const custoTotalCalculado =
        totalDistribuidora
        + valorDaEmpresa;


    const valorEconomia =
        totalSemGeracao
        - custoTotalCalculado;


    let percentualEconomia = 0;

    if (totalSemGeracao > 0) {

        percentualEconomia =
            (
                valorEconomia
                / totalSemGeracao
            ) * 100;
    }


    resumoEmpresa.textContent =
        formatarMoeda(
            valorDaEmpresa
        );


    custoTotal.textContent =
        formatarMoeda(
            custoTotalCalculado
        );


    economia.textContent =
        formatarMoeda(
            valorEconomia
        );


    percentual.textContent =
        `${percentualEconomia.toLocaleString(
            "pt-BR",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        )}%`;
}


// =========================================================
// ALTERAÇÃO DO VALOR DA EMPRESA
// =========================================================

valorEmpresa.addEventListener(
    "input",
    atualizarCalculo
);