
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import CommentReplies from './components/CommentReplies.vue'

const API = '/api/comments/'

const comments = ref([])
const loading = ref(false)
const sending = ref(false)
const error = ref('')
const message = ref('')
const page = ref(1)
const total = ref(0)
const ordering = ref('-created_at')
const captcha = ref(null)
const preview = ref(false)
const replyTo = ref(null)
const file = ref(null)
const modal = ref(null)

const form = ref({
  user_name: '',
  email: '',
  home_page: '',
  text: '',
  captcha_value: '',
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(total.value / 25))
)

const t = (ua, ru, en) => `${ua} / ${ru} / ${en}`

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[char])
}

// Отображаем только разрешённые HTML-теги.
function safeHtml(value) {
  const doc = new DOMParser().parseFromString(
    `<div>${value || ''}</div>`,
    'text/html'
  )

  const allowed = new Set(['a', 'code', 'i', 'strong'])

  function clean(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      return escapeHtml(node.textContent)
    }

    if (node.nodeType !== Node.ELEMENT_NODE) return ''

    const tag = node.tagName.toLowerCase()
    const content = Array.from(node.childNodes)
      .map(clean)
      .join('')

    if (!allowed.has(tag)) {
      return escapeHtml(node.outerHTML)
    }

    if (tag === 'a') {
      const href = node.getAttribute('href') || ''
      let valid = false

      try {
        const url = new URL(href)
        valid = ['http:', 'https:'].includes(url.protocol)
      } catch {
        valid = false
      }

      if (!valid) return content

      const title = escapeHtml(node.getAttribute('title') || '')

      return `<a href="${escapeHtml(href)}"
        title="${title}"
        target="_blank"
        rel="noopener noreferrer">${content}</a>`
    }

    return `<${tag}>${content}</${tag}>`
  }

  return Array.from(doc.body.firstElementChild.childNodes)
    .map(clean)
    .join('')
}

async function loadComments() {
  loading.value = true
  error.value = ''

  try {
    const params = new URLSearchParams({
      page: page.value,
      ordering: ordering.value,
    })

    const response = await fetch(`${API}?${params}`)

    if (!response.ok) {
      throw new Error('API error')
    }

    const data = await response.json()

    comments.value = data.results || []
    total.value = data.count || 0

  } catch {
    error.value = t(
      'Не вдалося завантажити коментарі',
      'Не удалось загрузить комментарии',
      'Failed to load comments'
    )
  } finally {
    loading.value = false
  }
}

async function loadCaptcha() {
  try {
    const response = await fetch(`${API}captcha/`)

    if (!response.ok) {
      throw new Error('CAPTCHA error')
    }

    const data = await response.json()

    // Используем локальный адрес через прокси Vite.
    const imageUrl = new URL(
      data.captcha_image,
      window.location.origin
    )

    captcha.value = {
      key: data.captcha_key,
      image: imageUrl.pathname + imageUrl.search,
    }

    form.value.captcha_value = ''

  } catch {
    captcha.value = null
    error.value = t(
      'Помилка завантаження CAPTCHA',
      'Ошибка загрузки CAPTCHA',
      'CAPTCHA loading error'
    )
  }
}

function insertTag(tag) {
  if (tag === 'a') {
    form.value.text +=
      '<a href="https://example.com" title="Link">Text</a>'
  } else {
    form.value.text += `<${tag}></${tag}>`
  }
}

function selectReply(comment) {
  replyTo.value = comment
  preview.value = false

  document.getElementById('comment-form')?.scrollIntoView({
    behavior: 'smooth',
  })
}

function resetForm() {
  form.value = {
    user_name: '',
    email: '',
    home_page: '',
    text: '',
    captcha_value: '',
  }

  file.value = null
  replyTo.value = null
  preview.value = false

  const input = document.getElementById('attachment')
  if (input) input.value = ''
}

function validateForm() {
  if (!/^[A-Za-z0-9]+$/.test(form.value.user_name)) {
    return t(
      'Ім’я: лише латинські літери та цифри',
      'Имя: только латинские буквы и цифры',
      'Username: Latin letters and numbers only'
    )
  }

  const emailValid =
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.value.email)

  if (!emailValid) {
    return t(
      'Перевірте адресу електронної пошти',
      'Проверьте адрес электронной почты',
      'Check your email address'
    )
  }

  if (form.value.home_page) {
    try {
      const url = new URL(form.value.home_page)

      if (!['http:', 'https:'].includes(url.protocol)) {
        throw new Error('Invalid URL')
      }
    } catch {
      return t(
        'Вкажіть правильну адресу сайту',
        'Укажите правильный адрес сайта',
        'Enter a valid website URL'
      )
    }
  }

  if (!form.value.text.trim()) {
    return t(
      'Введіть коментар',
      'Введите комментарий',
      'Enter a comment'
    )
  }

  if (!form.value.captcha_value.trim()) {
    return t(
      'Введіть CAPTCHA',
      'Введите CAPTCHA',
      'Enter CAPTCHA'
    )
  }

  if (file.value) {
    const extension = file.value.name
      .split('.')
      .pop()
      .toLowerCase()

    if (!['jpg', 'jpeg', 'png', 'gif', 'txt'].includes(extension)) {
      return t(
        'Недозволений формат файлу',
        'Недопустимый формат файла',
        'Unsupported file format'
      )
    }

    const limit = extension === 'txt'
      ? 100 * 1024
      : 10 * 1024 * 1024

    if (file.value.size > limit) {
      return t(
        'Файл перевищує допустимий розмір',
        'Файл превышает допустимый размер',
        'File exceeds the allowed size'
      )
    }
  }

  return ''
}

async function submitComment() {
  error.value = ''
  message.value = ''

  const validationError = validateForm()

  if (validationError) {
    error.value = validationError
    return
  }

  if (!captcha.value) {
    await loadCaptcha()
    return
  }

  sending.value = true

  const data = new FormData()
  data.append('user_name', form.value.user_name)
  data.append('email', form.value.email)
  data.append('home_page', form.value.home_page)
  data.append('text', form.value.text)
  data.append('captcha_key', captcha.value.key)
  data.append('captcha_value', form.value.captcha_value)

  if (replyTo.value) {
    data.append('parent', replyTo.value.id)
  }

  if (file.value) {
    data.append('attachment', file.value)
  }

  try {
    const response = await fetch(API, {
      method: 'POST',
      body: data,
    })

    const result = await response.json()

    if (!response.ok) {
      const details = Object.values(result)
        .flat()
        .join(' ')

      throw new Error(
        details || t(
          'Помилка перевірки даних',
          'Ошибка проверки данных',
          'Validation error'
        )
      )
    }

    resetForm()

    message.value = t(
      'Коментар успішно додано',
      'Комментарий успешно добавлен',
      'Comment created successfully'
    )

    page.value = 1
    await loadComments()

  } catch (err) {
    error.value = err.message
  } finally {
    sending.value = false
    await loadCaptcha()
  }
}

function changeSort() {
  page.value = 1
  loadComments()
}

function changePage(next) {
  if (next < 1 || next > totalPages.value) return

  page.value = next
  loadComments()

  window.scrollTo({
    top: 0,
    behavior: 'smooth',
  })
}

function mediaUrl(url) {
  if (!url) return ''

  try {
    const parsed = new URL(url, window.location.origin)

    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return ''
    }

    // Локальные файлы: PyCharm и Docker
    if (
      parsed.origin === window.location.origin &&
      parsed.pathname.startsWith('/media/')
    ) {
      return parsed.pathname + parsed.search
    }

    // Облачные файлы: Cloudinary
    if (
      parsed.protocol === 'https:' &&
      parsed.hostname === 'res.cloudinary.com' &&
      /^\/[^/]+\/(image|raw)\/upload\//.test(parsed.pathname)
    ) {
      return parsed.href
    }

    return ''
  } catch {
    return ''
  }
}

function isImage(url) {
  return /\.(jpg|jpeg|png|gif)$/i.test(
    mediaUrl(url).split('?')[0]
  )
}

function openAttachment(attachment) {
  const url = typeof attachment === 'string'
    ? attachment
    : attachment?.attachment_url

  const commentId = typeof attachment === 'object' && attachment !== null
    ? attachment.id
    : null

  const safe = mediaUrl(url)
  if (!safe) return

  // Изображения открываем в модальном окне
  if (isImage(url)) {
    modal.value = safe
    return
  }

  // TXT открываем через Django с кодировкой UTF-8
  const pathname = new URL(safe, window.location.origin).pathname

  if (
    pathname.toLowerCase().endsWith('.txt') &&
    Number.isSafeInteger(commentId) &&
    commentId > 0
  ) {
    window.open(
      `${API}${commentId}/attachment/txt/`,
      '_blank',
      'noopener,noreferrer'
    )
    return
  }

  window.open(safe, '_blank', 'noopener,noreferrer')
}

function formatDate(value) {
  return new Date(value).toLocaleString('uk-UA')
}

let socket = null
let reconnectTimer = null
let reconnectAttempts = 0
let stopped = false

function connectWebSocket() {
  if (stopped) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/comments/`

  socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    reconnectAttempts = 0
    console.log('WebSocket connected')
  }

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'comment_created') {
        loadComments()
      }
    } catch {
      console.error('Invalid WebSocket message')
    }
  }

  socket.onclose = () => {
    if (!stopped) {
      const delay = Math.min(1000 * 2 ** reconnectAttempts, 10000)
      reconnectAttempts += 1
      reconnectTimer = setTimeout(connectWebSocket, delay)
    }
  }

  socket.onerror = () => {
    socket?.close()
  }
}

onMounted(async () => {
  await Promise.all([
    loadComments(),
    loadCaptcha(),
  ])

  connectWebSocket()
})

onUnmounted(() => {
  stopped = true
  clearTimeout(reconnectTimer)
  socket?.close()
})
</script>

<template>
  <div class="app">
    <header class="header">
      <h1>Comments SPA</h1>
      <p>
        {{ t(
          'Коментарі та відповіді',
          'Комментарии и ответы',
          'Comments and replies'
        ) }}
      </p>
    </header>

    <main class="container">
      <section id="comment-form" class="panel">
        <h2>
          {{ replyTo
            ? t(
                'Відповідь на коментар',
                'Ответ на комментарий',
                'Reply to comment'
              )
            : t(
                'Новий коментар',
                'Новый комментарий',
                'New comment'
              )
          }}
        </h2>

        <div v-if="replyTo" class="reply-banner">
          {{ t('Відповідь для', 'Ответ для', 'Reply to') }}:
          <strong>{{ replyTo.user_name }}</strong>

          <button type="button" @click="replyTo = null">
            ✕
          </button>
        </div>

        <form @submit.prevent="submitComment">
          <div class="form-grid">
            <label>
              {{ t("Ім'я", 'Имя', 'Username') }} *
              <input
                v-model="form.user_name"
                maxlength="100"
                required
                pattern="[A-Za-z0-9]+"
              />
            </label>

            <label>
              Email *
              <input
                v-model="form.email"
                type="email"
                required
              />
            </label>
          </div>

          <label>
            {{ t(
              'Домашня сторінка',
              'Домашняя страница',
              'Home page'
            ) }}

            <input
              v-model="form.home_page"
              type="url"
              placeholder="https://example.com"
            />
          </label>

          <label>
            {{ t(
              'Текст коментаря',
              'Текст комментария',
              'Comment text'
            ) }} *
          </label>

          <div class="toolbar">
            <button
              v-for="tag in ['i', 'strong', 'code', 'a']"
              :key="tag"
              type="button"
              @click="insertTag(tag)"
            >
              {{ tag }}
            </button>
          </div>

          <textarea
            v-model="form.text"
            rows="6"
            required
            :placeholder="t(
              'Напишіть коментар...',
              'Напишите комментарий...',
              'Write a comment...'
            )"
          ></textarea>

          <button
            class="secondary"
            type="button"
            @click="preview = !preview"
          >
            {{ t(
              'Попередній перегляд',
              'Предпросмотр',
              'Preview'
            ) }}
          </button>

          <div v-if="preview" class="preview">
            <h3>
              {{ t(
                'Попередній перегляд',
                'Предпросмотр',
                'Preview'
              ) }}
            </h3>

            <div v-html="safeHtml(form.text)"></div>
          </div>

          <label class="file-label" for="attachment">
            {{ t(
              'Прикріпити файл',
              'Прикрепить файл',
              'Attach file'
            ) }}
            (JPG, PNG, GIF, TXT)
          </label>

          <input
            id="attachment"
            type="file"
            accept=".jpg,.jpeg,.png,.gif,.txt"
            @change="file = $event.target.files?.[0] || null"
          />

          <div class="captcha-box">
            <div>
              <strong>CAPTCHA *</strong>

              <div v-if="captcha">
                <img
                  :src="captcha.image"
                  alt="CAPTCHA"
                  class="captcha-image"
                />
              </div>

              <button
                class="secondary"
                type="button"
                @click="loadCaptcha"
              >
                {{ t('Оновити', 'Обновить', 'Refresh') }}
              </button>
            </div>

            <label>
              {{ t(
                'Введіть символи',
                'Введите символы',
                'Enter characters'
              ) }}

              <input
                v-model="form.captcha_value"
                required
              />
            </label>
          </div>

          <div v-if="error" class="alert error">
            {{ error }}
          </div>

          <div v-if="message" class="alert success">
            {{ message }}
          </div>

          <button
            class="primary"
            type="submit"
            :disabled="sending"
          >
            {{ sending
              ? t('Надсилання...', 'Отправка...', 'Sending...')
              : t('Надіслати', 'Отправить', 'Submit')
            }}
          </button>
        </form>
      </section>

      <section class="panel">
        <div class="list-header">
          <h2>
            {{ t('Коментарі', 'Комментарии', 'Comments') }}
            ({{ total }})
          </h2>

          <label class="sort-label">
            {{ t(
              'Сортування',
              'Сортировка',
              'Sort'
            ) }}

            <select
              v-model="ordering"
              @change="changeSort"
            >
              <option value="-created_at">Date ↓</option>
              <option value="created_at">Date ↑</option>
              <option value="user_name">Username ↑</option>
              <option value="-user_name">Username ↓</option>
              <option value="email">Email ↑</option>
              <option value="-email">Email ↓</option>
            </select>
          </label>
        </div>

        <p v-if="loading">
          {{ t(
            'Завантаження...',
            'Загрузка...',
            'Loading...'
          ) }}
        </p>

        <div v-else-if="!comments.length" class="empty">
          {{ t(
            'Коментарів поки немає',
            'Комментариев пока нет',
            'No comments yet'
          ) }}
        </div>

        <div v-else class="table-wrap">
          <table class="comments-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Date</th>
                <th>Comment</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="comment in comments"
                :key="comment.id"
              >
                <td>{{ comment.user_name }}</td>

                <td>{{ comment.email }}</td>

                <td>{{ formatDate(comment.created_at) }}</td>

                <td>
                  <div
                    class="comment-text"
                    v-html="safeHtml(comment.text)"
                  ></div>

                  <button
                    v-if="comment.attachment_url"
                    type="button"
                    class="link-button"
                    @click="openAttachment(comment)"
                  >
                    📎 {{ t(
                      'Переглянути файл',
                      'Посмотреть файл',
                      'View file'
                    ) }}
                  </button>

                  <button
                    type="button"
                    class="link-button"
                    @click="selectReply(comment)"
                  >
                    ↩ {{ t(
                      'Відповісти',
                      'Ответить',
                      'Reply'
                    ) }}
                  </button>

                  <!-- Рекурсивные ответы любой глубины -->
                  <CommentReplies
                    v-if="comment.replies?.length"
                    :replies="comment.replies"
                    @reply="selectReply"
                    @attachment="openAttachment"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pagination">
          <button
            class="secondary"
            type="button"
            :disabled="page <= 1"
            @click="changePage(page - 1)"
          >
            ←
          </button>

          <span>
            {{ t('Сторінка', 'Страница', 'Page') }}
            {{ page }} / {{ totalPages }}
          </span>

          <button
            class="secondary"
            type="button"
            :disabled="page >= totalPages"
            @click="changePage(page + 1)"
          >
            →
          </button>
        </div>
      </section>
    </main>

    <div
      v-if="modal"
      class="modal"
      role="dialog"
      aria-modal="true"
      @click.self="modal = null"
    >
      <button
        class="modal-close"
        type="button"
        @click="modal = null"
      >
        ✕
      </button>

      <img :src="modal" alt="Attachment" />
    </div>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: #f2f5f9;
  color: #273444;
  font-family: Arial, sans-serif;
  line-height: 1.5;
}

button,
input,
select,
textarea {
  font: inherit;
}

button {
  cursor: pointer;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.header {
  background: #243b53;
  color: white;
  padding: 25px 16px;
  text-align: center;
}

.header h1 {
  margin: 0;
}

.header p {
  margin-bottom: 0;
  color: #d9e2ec;
}

.container {
  width: min(1100px, 95%);
  margin: 30px auto;
}

.panel {
  background: white;
  padding: 25px;
  margin-bottom: 25px;
  border-radius: 12px;
  box-shadow: 0 4px 18px #00000012;
}

h2 {
  margin-top: 0;
}

label {
  display: block;
  margin: 12px 0;
  font-weight: 600;
}

input:not([type="file"]),
textarea,
select {
  display: block;
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 7px;
  padding: 10px;
  margin-top: 5px;
  color: #273444;
  background: #ffffff;
}

textarea {
  resize: vertical;
  min-height: 130px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.primary {
  color: white;
  background: #2563eb;
  border: none;
  border-radius: 7px;
  padding: 12px 22px;
  margin-top: 15px;
}

.secondary,
.toolbar button {
  color: #243b53;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #f8fafc;
  padding: 8px 12px;
}

.toolbar {
  display: flex;
  gap: 8px;
  margin: 10px 0;
  flex-wrap: wrap;
}

.preview {
  margin: 15px 0;
  border: 1px dashed #94a3b8;
  background: #f8fafc;
  padding: 15px;
  overflow-wrap: anywhere;
}

.file-label {
  margin-top: 22px;
}

.captcha-box {
  display: flex;
  gap: 30px;
  align-items: end;
  margin: 25px 0;
  flex-wrap: wrap;
}

.captcha-box > * {
  flex: 1;
  min-width: 200px;
}

.captcha-image {
  display: block;
  margin: 10px 0;
  width: 220px;
  max-width: 100%;
  height: auto;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #ffffff;
  padding: 6px;
}

.alert {
  padding: 12px;
  border-radius: 6px;
  margin: 15px 0;
  overflow-wrap: anywhere;
}

.error {
  background: #fee2e2;
  color: #991b1b;
}

.success {
  background: #dcfce7;
  color: #166534;
}

.reply-banner {
  background: #eff6ff;
  padding: 12px;
  margin-bottom: 15px;
  border-radius: 6px;
}

.reply-banner button {
  float: right;
  border: none;
  background: transparent;
  color: #243b53;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.sort-label {
  min-width: 200px;
}

.table-wrap {
  overflow-x: auto;
}

.comments-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}

.comments-table th {
  background: #e9eff6;
  text-align: left;
}

.comments-table th,
.comments-table td {
  padding: 12px;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: top;
}

.comments-table td:last-child {
  min-width: 280px;
}

.comment-text {
  overflow-wrap: anywhere;
}

.link-button {
  background: none;
  border: none;
  color: #2563eb;
  padding: 4px 8px 4px 0;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 18px;
  padding-top: 25px;
}

.empty {
  padding: 20px;
  text-align: center;
  color: #64748b;
}

.modal {
  position: fixed;
  inset: 0;
  background: #000000dc;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 30px;
}

.modal img {
  max-width: 95%;
  max-height: 90vh;
  object-fit: contain;
}

.modal-close {
  position: absolute;
  top: 20px;
  right: 25px;
  color: white;
  background: none;
  border: none;
  font-size: 30px;
}

@media (max-width: 700px) {
  .form-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .panel {
    padding: 15px;
  }
}
</style>
