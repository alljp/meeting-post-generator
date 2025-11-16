import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Plus, Edit2, Trash2, ToggleLeft, ToggleRight, Loader2, Sparkles } from 'lucide-react'
import { useToastContext } from '../contexts/ToastContext'
import api from '../lib/api'
import AutomationForm from './AutomationForm'
import ConfirmDialog from './ConfirmDialog'

interface Automation {
  id: number
  name: string
  platform: string
  prompt_template: string
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export default function AutomationList() {
  const queryClient = useQueryClient()
  const { success, error: showError } = useToastContext()
  const [editingId, setEditingId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: number | null; open: boolean }>({
    id: null,
    open: false,
  })

  const { data: automations, isLoading } = useQuery<Automation[]>({
    queryKey: ['automations'],
    queryFn: async () => {
      const response = await api.get('/settings/automations')
      return response.data
    },
  })

  const toggleMutation = useMutation({
    mutationFn: async ({ id, isActive }: { id: number; isActive: boolean }) => {
      const response = await api.patch(`/settings/automations/${id}`, { is_active: !isActive })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/settings/automations/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] })
      success('Automation deleted successfully')
      setDeleteConfirm({ id: null, open: false })
    },
    onError: (error: any) => {
      showError(`Failed to delete automation: ${error.response?.data?.detail || error.message}`)
      setDeleteConfirm({ id: null, open: false })
    },
  })

  const handleEdit = (automation: Automation) => {
    setEditingId(automation.id)
    setShowForm(true)
  }

  const handleDelete = (id: number) => {
    setDeleteConfirm({ id, open: true })
  }

  const confirmDelete = () => {
    if (deleteConfirm.id !== null) {
      deleteMutation.mutate(deleteConfirm.id)
    }
  }

  const handleFormClose = () => {
    setShowForm(false)
    setEditingId(null)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
      </div>
    )
  }

  const linkedinAutomation = automations?.find(a => a.platform === 'linkedin')
  const facebookAutomation = automations?.find(a => a.platform === 'facebook')

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Post Generation Automations</h3>
          <p className="text-sm text-gray-500 mt-1">
            Configure how AI generates posts for each platform. You can create one automation per platform.
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          disabled={showForm}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Automation
        </button>
      </div>

      {showForm && (
        <AutomationForm
          automationId={editingId}
          onClose={handleFormClose}
          onSuccess={() => {
            handleFormClose()
            queryClient.invalidateQueries({ queryKey: ['automations'] })
          }}
        />
      )}

      <div className="space-y-3">
        {/* LinkedIn Automation */}
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h4 className="font-medium text-gray-900">LinkedIn</h4>
                {linkedinAutomation && (
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      linkedinAutomation.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {linkedinAutomation.is_active ? 'Active' : 'Inactive'}
                  </span>
                )}
              </div>
              {linkedinAutomation ? (
                <div className="space-y-2">
                  <p className="text-sm text-gray-700 font-medium">{linkedinAutomation.name}</p>
                  <p className="text-sm text-gray-500 line-clamp-2">
                    {linkedinAutomation.prompt_template}
                  </p>
                  <div className="flex items-center gap-2 pt-2">
                    <button
                      onClick={() => toggleMutation.mutate({ id: linkedinAutomation.id, isActive: linkedinAutomation.is_active })}
                      disabled={toggleMutation.isPending}
                      className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
                    >
                      {linkedinAutomation.is_active ? (
                        <ToggleRight className="w-5 h-5 text-green-600" />
                      ) : (
                        <ToggleLeft className="w-5 h-5 text-gray-400" />
                      )}
                      <span className="ml-1">
                        {linkedinAutomation.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </button>
                    <button
                      onClick={() => handleEdit(linkedinAutomation)}
                      className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
                    >
                      <Edit2 className="w-4 h-4 mr-1" />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(linkedinAutomation.id)}
                      className="inline-flex items-center text-sm text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Delete
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Sparkles className="w-4 h-4" />
                  <span>No automation configured</span>
                  <button
                    onClick={() => {
                      setShowForm(true)
                      setEditingId(null)
                    }}
                    className="text-blue-600 hover:text-blue-700 ml-2"
                  >
                    Create one
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Facebook Automation */}
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h4 className="font-medium text-gray-900">Facebook</h4>
                {facebookAutomation && (
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      facebookAutomation.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {facebookAutomation.is_active ? 'Active' : 'Inactive'}
                  </span>
                )}
              </div>
              {facebookAutomation ? (
                <div className="space-y-2">
                  <p className="text-sm text-gray-700 font-medium">{facebookAutomation.name}</p>
                  <p className="text-sm text-gray-500 line-clamp-2">
                    {facebookAutomation.prompt_template}
                  </p>
                  <div className="flex items-center gap-2 pt-2">
                    <button
                      onClick={() => toggleMutation.mutate({ id: facebookAutomation.id, isActive: facebookAutomation.is_active })}
                      disabled={toggleMutation.isPending}
                      className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
                    >
                      {facebookAutomation.is_active ? (
                        <ToggleRight className="w-5 h-5 text-green-600" />
                      ) : (
                        <ToggleLeft className="w-5 h-5 text-gray-400" />
                      )}
                      <span className="ml-1">
                        {facebookAutomation.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </button>
                    <button
                      onClick={() => handleEdit(facebookAutomation)}
                      className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
                    >
                      <Edit2 className="w-4 h-4 mr-1" />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(facebookAutomation.id)}
                      className="inline-flex items-center text-sm text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Delete
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Sparkles className="w-4 h-4" />
                  <span>No automation configured</span>
                  <button
                    onClick={() => {
                      setShowForm(true)
                      setEditingId(null)
                    }}
                    className="text-blue-600 hover:text-blue-700 ml-2"
                  >
                    Create one
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <ConfirmDialog
        isOpen={deleteConfirm.open}
        title="Delete Automation"
        message="Are you sure you want to delete this automation? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        onConfirm={confirmDelete}
        onCancel={() => setDeleteConfirm({ id: null, open: false })}
      />
    </div>
  )
}

