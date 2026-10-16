<script setup>
defineOptions({ name: 'CommentReplies' })

defineProps({
  replies: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['reply', 'attachment'])

function formatDate(value) {
  return new Date(value).toLocaleString('uk-UA')
}

function safeText(value) {
  return String(value ?? '')
}
</script>

<template>
  <div v-if="replies.length" class="replies-tree">
    <div
      v-for="reply in replies"
      :key="reply.id"
      class="reply-item"
    >
      <div class="reply-header">
        <strong>{{ reply.user_name }}</strong>
        <small>{{ formatDate(reply.created_at) }}</small>
      </div>

      <div class="reply-text">{{ safeText(reply.text) }}</div>

      <div class="reply-actions">
        <button type="button" @click="emit('reply', reply)">
          ↩ Відповісти / Ответить / Reply
        </button>

        <button
          v-if="reply.attachment_url"
          type="button"
          @click="emit('attachment', reply)"
        >
          📎 Переглянути / Посмотреть / View
        </button>
      </div>

      <CommentReplies
        v-if="reply.replies?.length"
        :replies="reply.replies"
        @reply="emit('reply', $event)"
        @attachment="emit('attachment', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.replies-tree {
  margin-top: 12px;
  margin-left: 14px;
  padding-left: 14px;
  border-left: 3px solid #cbd5e1;
}

.reply-item {
  margin: 10px 0;
  padding: 12px;
  border-radius: 7px;
  background: #f8fafc;
  overflow-wrap: anywhere;
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.reply-header small {
  color: #64748b;
}

.reply-text {
  margin-top: 8px;
  white-space: pre-wrap;
}

.reply-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.reply-actions button {
  border: 0;
  background: transparent;
  color: #2563eb;
  padding: 4px 0;
  cursor: pointer;
}
</style>