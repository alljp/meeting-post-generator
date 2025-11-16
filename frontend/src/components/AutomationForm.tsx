import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X, Save, Loader2 } from 'lucide-react'
import { useToastContext } from '../contexts/ToastContext'
import api from '@/lib/api'

const automationSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
  platform: z.enum(['linkedin', 'facebook'], {
    required_error: 'Platform is required',
  }),
  prompt_template: z.string().min(10, 'Prompt template must be at least 10 characters'),
  is_active: z.boolean().default(true),
})

type AutomationFormData = z.infer<typeof automationSchema>

interface AutomationFormProps {
  automationId?: number | null
  onClose: () => void
  onSuccess: () => void
}

export default function AutomationForm({ automationId, onClose, onSuccess }: AutomationFormProps) {
  const queryClient = useQueryClient()
  const { success, error: showError } = useToastContext()

  // Fetch existing automation if editing
  const { data: existingAutomation, isLoading: isLoadingExisting } = useQuery({
    queryKey: ['automations', automationId],
    queryFn: async () => {
      const response = await api.get('/settings/automations')
      const automations = response.data
      return automations.find((a: any) => a.id === automationId)
    },
    enabled: !!automationId,
  })

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setValue,
  } = useForm<AutomationFormData>({
    resolver: zodResolver(automationSchema),
    defaultValues: {
      name: '',
      platform: 'linkedin',
      prompt_template: '',
      is_active: true,
    },
    values: existingAutomation
      ? {
          name: existingAutomation.name,
          platform: existingAutomation.platform,
          prompt_template: existingAutomation.prompt_template,
          is_active: existingAutomation.is_active,
        }
      : undefined,
  })

  const selectedPlatform = watch('platform')

  const createMutation = useMutation({
    mutationFn: async (data: AutomationFormData) => {
      const response = await api.post('/settings/automations', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] })
      onSuccess()
      success('Automation created successfully!')
    },
    onError: (error: any) => {
      showError(`Failed to create automation: ${error.response?.data?.detail || error.message}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: async (data: Partial<AutomationFormData>) => {
      const response = await api.patch(`/settings/automations/${automationId}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] })
      onSuccess()
      success('Automation updated successfully!')
    },
    onError: (error: any) => {
      showError(`Failed to update automation: ${error.response?.data?.detail || error.message}`)
    },
  })

  const onSubmit = (data: AutomationFormData) => {
    if (automationId) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  // Default prompt templates
  const defaultPrompts = {
    linkedin: `You are creating a professional LinkedIn post based on a meeting transcript.

Meeting Title: {meeting_title}
Meeting Transcript: {transcript}

Create an engaging LinkedIn post that:
- Highlights key insights or takeaways
- Is professional and business-focused
- Encourages engagement and discussion
- Uses 1-3 relevant hashtags
- Is appropriate for a professional network

Generate only the post content, no additional formatting.`,
    facebook: `You are creating an engaging Facebook post based on a meeting transcript.

Meeting Title: {meeting_title}
Meeting Transcript: {transcript}

Create a Facebook post that:
- Is conversational and relatable
- Highlights interesting points or insights
- Encourages community engagement
- Uses 1-2 relevant hashtags
- Is appropriate for a social media audience

Generate only the post content, no additional formatting.`,
  }

  const handleUseDefault = () => {
    setValue('prompt_template', defaultPrompts[selectedPlatform])
  }

  if (isLoadingExisting) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {automationId ? 'Edit Automation' : 'Create Automation'}
        </h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Automation Name
          </label>
          <input
            type="text"
            id="name"
            {...register('name')}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
            placeholder="e.g., Marketing Content Generator"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="platform" className="block text-sm font-medium text-gray-700 mb-1">
            Platform
          </label>
          <select
            id="platform"
            {...register('platform')}
            disabled={!!automationId}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="linkedin">LinkedIn</option>
            <option value="facebook">Facebook</option>
          </select>
          {errors.platform && (
            <p className="mt-1 text-sm text-red-600">{errors.platform.message}</p>
          )}
          {automationId && (
            <p className="mt-1 text-xs text-gray-500">Platform cannot be changed after creation</p>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label htmlFor="prompt_template" className="block text-sm font-medium text-gray-700">
              Prompt Template
            </label>
            {!automationId && (
              <button
                type="button"
                onClick={handleUseDefault}
                className="text-xs text-blue-600 hover:text-blue-700"
              >
                Use Default Template
              </button>
            )}
          </div>
          <p className="text-xs text-gray-500 mb-2">
            Use {'{transcript}'} and {'{meeting_title}'} as placeholders that will be replaced with actual values.
          </p>
          <textarea
            id="prompt_template"
            {...register('prompt_template')}
            rows={10}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border font-mono text-sm"
            placeholder="Enter your prompt template here..."
          />
          {errors.prompt_template && (
            <p className="mt-1 text-sm text-red-600">{errors.prompt_template.message}</p>
          )}
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_active"
            {...register('is_active')}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
            Active (automation will be used when generating posts)
          </label>
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || createMutation.isPending || updateMutation.isPending}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {(isSubmitting || createMutation.isPending || updateMutation.isPending) ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {automationId ? 'Update' : 'Create'} Automation
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

