# API Contract Convention

Dokumen ini menjelaskan response envelope Reservation Chatbot. Struktur
diadaptasi dari kontrak Kotoba Hub, tetapi hanya mengambil field yang digunakan
project ini. Definisi endpoint dan schema normatif tetap berada di
[openapi.yml](openapi.yml).

## Success response

Semua response berhasil memiliki `status` dan object `data`:

```json
{
  "status": {
    "code": 120000000,
    "message": "Success.",
    "errorDetails": []
  },
  "data": {
    "conversation_id": "01K1A2B3C4D5E6F7G8H9J0K1M2"
  }
}
```

Aturan:

- `data` selalu object, bukan array atau scalar pada root.
- Koleksi memakai nama eksplisit di dalam `data`, misalnya `messages`,
  `services`, atau `slots`.
- `status.errorDetails` selalu array kosong pada response berhasil.
- HTTP 200 memakai code `120000000`; HTTP 201 memakai `120100000`.
- Endpoint MVP selalu memiliki return value, sehingga empty success envelope
  belum diperlukan.

## Error response

Response gagal hanya memiliki `status` dan tidak mengembalikan `data`:

```json
{
  "status": {
    "code": 142200002,
    "message": "Nilai slot tidak valid.",
    "errorDetails": [
      {
        "field": "customer_id",
        "message": "ID pelanggan harus tepat 10 digit angka."
      }
    ]
  }
}
```

Aturan:

- `status.message` aman ditampilkan kepada pengguna.
- `errorDetails` diisi untuk error field/validation; error non-field memakai
  array kosong.
- HTTP status tetap menjadi sumber utama kategori keberhasilan/kegagalan.
- `status.code` adalah identifier aplikasi yang stabil, bukan pengganti HTTP
  status.
- Invalid slot menghasilkan HTTP 422. State dan slot valid sebelumnya tetap
  disimpan server, tetapi response mengikuti error envelope.
- Tidak ada field `retryable`. HTTP 429 menggunakan header `Retry-After`;
  HTTP 503 dapat dicoba kembali dengan backoff.

## Application code

Format code adalah 9 digit:

```text
[interface][HTTP status][domain][specific]
```

Project ini hanya memerlukan interface REST `1` dan shared domain `00`.

| Code | HTTP | Arti |
|---:|---:|---|
| `120000000` | 200 | Success |
| `120100000` | 201 | Created |
| `140400001` | 404 | Conversation tidak ditemukan |
| `140400002` | 404 | Tiket tidak ditemukan |
| `140900001` | 409 | Operasi tidak sesuai state conversation |
| `141000001` | 410 | Conversation kedaluwarsa |
| `141300001` | 413 | Attachment terlalu besar |
| `141500001` | 415 | Tipe attachment tidak didukung |
| `142200001` | 422 | Validasi payload/schema |
| `142200002` | 422 | Validasi slot/domain |
| `142900001` | 429 | Rate limit terlampaui |
| `150000999` | 500 | Kesalahan internal tidak terduga |
| `150300001` | 503 | Dependency runtime belum siap |
| `150300002` | 503 | Model NLP belum siap |

## Field yang sengaja tidak digunakan

- `traceId`: belum diperlukan untuk demo lokal dan observability MVP.
- `metadata.pagination`: tidak ada endpoint list yang membutuhkan pagination;
  katalog dan slot survei merupakan koleksi kecil berbatas.
- Auth/security envelope: autentikasi berada di luar scope MVP.
- Empty success response: semua endpoint saat ini mengembalikan object data.
