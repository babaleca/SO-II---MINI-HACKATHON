// O coordenador serve o estado e recebe os comandos.
// Para testar a interface sem backend, apontar URL_ESTADO para "estado_falso.json".
const URL_ESTADO = "/estado";
const URL_COMANDO = "/comando";
const INTERVALO = 300;

const PAREDE = "#", CORREDOR = "~", SAIDA = "E", INICIO = "S";
const ITENS = { L: "Lanterna", C: "Chave", R: "Retrato", B: "Boneca" };

const grade = document.getElementById("grade");
const pecas = document.getElementById("pecas");
const fichas = document.getElementById("fichas");
const corredor = document.getElementById("corredor");
const aviso = document.getElementById("aviso");

let mapaDesenhado = null;   // so redesenha a grade se o mapa mudar
const pecasNaTela = new Map();


function desenharMapa(mapa) {
  const chave = mapa.join("\n");
  if (chave === mapaDesenhado) return;
  mapaDesenhado = chave;

  grade.style.setProperty("--colunas", mapa[0].length);
  grade.innerHTML = "";

  for (const linha of mapa) {
    for (const c of linha) {
      const casa = document.createElement("div");
      casa.className = "casa";

      if (c === PAREDE) casa.classList.add("parede");
      else if (c === CORREDOR) casa.classList.add("corredor");
      else if (c === SAIDA) { casa.classList.add("saida"); casa.textContent = "E"; }
      else if (c === INICIO) { casa.classList.add("inicio"); casa.textContent = "S"; }
      else if (ITENS[c]) {
        casa.classList.add("item");
        casa.textContent = c;
        casa.title = ITENS[c];
      }
      grade.appendChild(casa);
    }
  }
}


function moverPecas(exploradores) {
  // le o tamanho real de uma casa, porque --cel usa clamp e varia com a tela
  const casa = grade.firstElementChild;
  if (!casa) return;
  const lado = casa.getBoundingClientRect().width;
  const vistos = new Set();

  for (const e of exploradores) {
    vistos.add(e.id);
    let peca = pecasNaTela.get(e.id);

    if (!peca) {
      peca = document.createElement("div");
      peca.className = "peca";
      peca.innerHTML = `<span class="marca">${e.id}</span>`;
      pecas.appendChild(peca);
      pecasNaTela.set(e.id, peca);
    }

    const [y, x] = e.pos;
    peca.style.transform = `translate(${x * lado}px, ${y * lado}px)`;
    peca.className = "peca " + e.status;
    peca.title = e.nome;
  }

  // tira do mapa quem foi finalizado e sumiu do estado
  for (const [id, peca] of pecasNaTela) {
    if (!vistos.has(id)) { peca.remove(); pecasNaTela.delete(id); }
  }
}


function desenharFichas(exploradores) {
  fichas.innerHTML = "";

  for (const e of exploradores) {
    const ficha = document.createElement("div");
    ficha.className = "ficha " + e.status + (e.completo ? " completo" : "");

    const tarefas = Object.entries(e.checklist)
      .map(([s, feito]) => `<span class="tarefa ${feito ? "feita" : ""}"
                                  title="${ITENS[s] || s}">${s}</span>`)
      .join("");

    ficha.innerHTML = `
      <div class="nome"><span>${e.nome}</span><span class="estado">${e.status}</span></div>
      <div class="tarefas">${tarefas}</div>
      <div class="acoes">
        <button data-acao="suspender" data-id="${e.id}">Suspender</button>
        <button data-acao="retomar" data-id="${e.id}">Retomar</button>
        <button data-acao="finalizar" data-id="${e.id}">Finalizar</button>
      </div>`;

    fichas.appendChild(ficha);
  }
}


async function enviarComando(acao, id) {
  try {
    await fetch(URL_COMANDO, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ acao: acao, id: id }),
    });
    aviso.textContent = "";
  } catch {
    aviso.textContent = "Coordenador nao respondeu";
  }
}


async function atualizar() {
  try {
    const r = await fetch(URL_ESTADO, { cache: "no-store" });
    const estado = await r.json();

    desenharMapa(estado.mapa);
    moverPecas(estado.exploradores);
    desenharFichas(estado.exploradores);

    corredor.textContent = estado.corredor_ocupado
      ? "Corredor estreito ocupado"
      : "Corredor estreito livre";
    corredor.classList.toggle("ocupado", estado.corredor_ocupado);
    aviso.textContent = "";
  } catch {
    aviso.textContent = "Sem conexao com o coordenador";
  }
}


fichas.addEventListener("click", (ev) => {
  const b = ev.target.closest("button");
  if (b) enviarComando(b.dataset.acao, Number(b.dataset.id));
});

document.getElementById("criar")
        .addEventListener("click", () => enviarComando("criar", null));

atualizar();
setInterval(atualizar, INTERVALO);
