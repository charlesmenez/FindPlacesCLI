import requests
import csv
import time
import re
from typing import List, Dict, Optional

API_KEY = "COLOQUE_SUA_API_AQUI"  # Substitua pela sua chave válida

def geocodificar_endereco(endereco: str) -> str:
    """Converte endereço em latitude e longitude usando a Geocoding API."""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": endereco, "key": API_KEY}
    resposta = requests.get(url, params=params).json()

    if resposta.get("status") == "OK" and resposta.get("results"):
        local = resposta["results"][0]["geometry"]["location"]
        return f"{local['lat']},{local['lng']}"
    else:
        raise ValueError(f"Endereço não encontrado ou inválido: {resposta.get('status')}")


def buscar_estabelecimentos(localizacao: str, termo: str, raio: int) -> List[Dict[str, Optional[str]]]:
    """Busca estabelecimentos próximos usando a Places API."""
    url_base = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": localizacao,
        "radius": raio,
        "keyword": termo,
        "key": API_KEY
    }

    estabelecimentos = []
    while True:
        resposta = requests.get(url_base, params=params).json()

        if resposta.get("status") not in ["OK", "ZERO_RESULTS"]:
            print(f"⚠ Erro ao buscar estabelecimentos: {resposta.get('status')}")
            break

        for lugar in resposta.get("results", []):
            place_id = lugar.get("place_id")
            detalhes = buscar_detalhes_estabelecimento(place_id)
            if detalhes:
                estabelecimentos.append(detalhes)

        next_page_token = resposta.get("next_page_token")
        if next_page_token:
            time.sleep(2)
            params = {
                "pagetoken": next_page_token,
                "key": API_KEY
            }
        else:
            break

    return estabelecimentos


def buscar_detalhes_estabelecimento(place_id: str) -> Dict[str, Optional[str]]:
    """Obtém detalhes adicionais de um local usando a Place Details API."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website",
        "key": API_KEY
    }

    resposta = requests.get(url, params=params).json()
    dados = resposta.get("result", {})

    telefone = dados.get("formatted_phone_number")
    whatsapp_link = gerar_link_whatsapp(telefone) if telefone else ""

    return {
        "Nome": dados.get("name"),
        "Endereço": dados.get("formatted_address"),
        "Telefone": telefone,
        "Site": dados.get("website"),
        "WhatsApp": whatsapp_link
    }


def gerar_link_whatsapp(telefone: str) -> str:
    """Gera link clicável para WhatsApp a partir do telefone com DDI."""
    numero_limpo = re.sub(r"\D", "", telefone)
    if not numero_limpo.startswith("55"):
        numero_limpo = "55" + numero_limpo
    return f"https://wa.me/{numero_limpo}"


def salvar_em_csv(lista: List[Dict[str, Optional[str]]], arquivo: str) -> None:
    """Salva dados em um arquivo CSV."""
    with open(arquivo, mode="w", newline="", encoding="utf-8") as f:
        campos = ["Nome", "Endereço", "Telefone", "Site", "WhatsApp"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for item in lista:
            writer.writerow(item)
    print(f"✅ Dados salvos com sucesso em '{arquivo}'.")


def main():
    print("🔧 Configuração de busca:\n")

    endereco = input("📍 Digite o endereço-base da busca: ").strip()
    termo_busca = input("🔎 Digite o termo de busca (ex: ar condicionado): ").strip()

    try:
        raio = int(input("📏 Digite o raio em metros (ex: 3000): ").strip())
        if raio <= 0:
            raise ValueError
    except ValueError:
        print("❌ Raio inválido. Usando valor padrão de 3000m.")
        raio = 3000

    nome_arquivo = input("💾 Digite o nome do arquivo CSV (ex: resultados.csv): ").strip()
    if not nome_arquivo:
        nome_arquivo = "estabelecimentos.csv"
    elif not nome_arquivo.endswith(".csv"):
        nome_arquivo += ".csv"

    try:
        print(f"\n📍 Geocodificando endereço: {endereco}")
        localizacao = geocodificar_endereco(endereco)

        print(f"🔍 Buscando estabelecimentos contendo '{termo_busca}' em um raio de {raio} metros...")
        resultados = buscar_estabelecimentos(localizacao, termo_busca, raio)

        print(f"💾 Salvando {len(resultados)} resultados no CSV...")
        salvar_em_csv(resultados, nome_arquivo)

    except Exception as e:
        print(f"❌ Erro durante execução: {e}")


if __name__ == "__main__":
    main()

