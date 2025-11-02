import React, { useMemo, useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Grid,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Stack,
  FormControlLabel,
  Switch,
  Tooltip,
  Divider,
} from '@mui/material'
import {
  People,
  Edit,
  PersonAdd,
  Block,
  CheckCircle,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useForm, Controller } from 'react-hook-form'
import { yupResolver } from '@hookform/resolvers/yup'
import * as yup from 'yup'
import toast from 'react-hot-toast'
import { useAuth } from '../contexts/AuthContext'
import {
  fetchUsers,
  fetchRoles,
  fetchAgencies,
  createUser,
  updateUser,
  UserSummary,
  Role,
  Agency,
  UpdateUserPayload,
} from '../services/users'

type FormMode = 'create' | 'edit'

type UserFormValues = {
  username: string
  email: string
  full_name?: string | null
  password?: string
  confirm_password?: string
  role_id: number
  agency_id: number
  is_active: boolean
}

const validationSchema = yup.object({
  username: yup.string().trim().required('Username is required'),
  email: yup.string().trim().email('Enter a valid email').required('Email is required'),
  full_name: yup.string().nullable(),
  password: yup.string().when('$isEdit', {
    is: true,
    then: schema => schema.optional(),
    otherwise: schema => schema.required('Password is required').min(8, 'Password must be at least 8 characters'),
  }),
  confirm_password: yup.string().when('$isEdit', {
    is: true,
    then: schema => schema.optional(),
    otherwise: schema => schema
      .required('Please confirm the password')
      .oneOf([yup.ref('password')], 'Passwords must match'),
  }),
  role_id: yup
    .number()
    .typeError('Select a role')
    .required('Role is required'),
  agency_id: yup
    .number()
    .typeError('Select an agency')
    .required('Agency is required'),
  is_active: yup.boolean(),
})

const getRoleColor = (role?: string | null) => {
  switch (role) {
    case 'super_admin':
      return 'error'
    case 'admin':
      return 'warning'
    case 'auditor':
      return 'info'
    case 'analyst':
      return 'success'
    case 'viewer':
      return 'default'
    default:
      return 'default'
  }
}

const getRoleLabel = (role?: string | null) => {
  switch (role) {
    case 'super_admin':
      return 'Super Admin'
    case 'admin':
      return 'Admin'
    case 'auditor':
      return 'Auditor'
    case 'analyst':
      return 'Analyst'
    case 'viewer':
      return 'Viewer'
    default:
      return role || 'Unknown'
  }
}

const UsersPage: React.FC = () => {
  const { user: currentUser } = useAuth()
  const queryClient = useQueryClient()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [formMode, setFormMode] = useState<FormMode>('create')
  const [selectedUser, setSelectedUser] = useState<UserSummary | null>(null)

  // Simple permission checks
  const canManageUsers = currentUser?.permissions?.users?.includes('create') || false
  const isSuperAdmin = currentUser?.role?.name === 'super_admin'

  const usersQuery = useQuery<UserSummary[]>(['users'], fetchUsers)
  const rolesQuery = useQuery<Role[]>(['roles'], fetchRoles, { enabled: canManageUsers })
  const agenciesQuery = useQuery<Agency[]>(['agencies'], fetchAgencies, { enabled: canManageUsers })

  const resolver = useMemo(
    () => yupResolver(validationSchema, { context: { isEdit: formMode === 'edit' } }) as any,
    [formMode]
  )

  const roleOptions = rolesQuery.data ?? []
  const agencyOptions: Agency[] = useMemo(() => {
    if (agenciesQuery.data?.length) {
      return agenciesQuery.data
    }

    if (currentUser?.agency) {
      return [{
        id: currentUser.agency.id,
        name: currentUser.agency.name,
        code: currentUser.agency.code ?? null,
        description: currentUser.agency.description ?? null,
        contact_email: currentUser.agency.contact_email ?? null,
      }]
    }

    if (currentUser?.agency_id) {
      return [{
        id: currentUser.agency_id,
        name: `Agency #${currentUser.agency_id}`,
        code: null,
        description: null,
        contact_email: null,
      }]
    }

    return []
  }, [agenciesQuery.data, currentUser?.agency, currentUser?.agency_id])

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UserFormValues>({
    defaultValues: {
      username: '',
      email: '',
      full_name: '',
      password: '',
      confirm_password: '',
      role_id: 0,
      agency_id: currentUser?.agency_id ?? 0,
      is_active: true,
    },
    resolver,
  })

  const createUserMutation = useMutation(createUser, {
    onSuccess: () => {
      toast.success('User created successfully')
      queryClient.invalidateQueries(['users'])
      setDialogOpen(false)
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail ?? 'Failed to create user'
      toast.error(message)
    },
  })

  const updateUserMutation = useMutation(
    ({ userId, payload }: { userId: number; payload: UpdateUserPayload }) => updateUser(userId, payload),
    {
      onSuccess: () => {
        toast.success('User updated successfully')
        queryClient.invalidateQueries(['users'])
        setDialogOpen(false)
      },
      onError: (error: any) => {
        const message = error?.response?.data?.detail ?? 'Failed to update user'
        toast.error(message)
      },
    }
  )

  const users = usersQuery.data ?? []
  const userStats = useMemo(() => ({
    total: users.length,
    active: users.filter(u => u.is_active).length,
    inactive: users.filter(u => !u.is_active).length,
    verified: users.filter(u => u.is_verified).length,
  }), [users])

  const handleOpenCreate = () => {
    if (!canManageUsers) return

    if (rolesQuery.isError) {
      toast.error('Unable to load roles. Please try again later.')
      return
    }

    if (isSuperAdmin && agenciesQuery.isError) {
      toast.error('Unable to load agencies. Please try again later.')
      return
    }

    if (!roleOptions.length) {
      toast.error('No roles available. Please create a role first.')
      return
    }

    if (isSuperAdmin && !agencyOptions.length) {
      toast.error('No agencies available. Please create an agency first.')
      return
    }

    setFormMode('create')
    setSelectedUser(null)
    reset({
      username: '',
      email: '',
      full_name: '',
      password: '',
      confirm_password: '',
      role_id: roleOptions[0]?.id ?? 0,
      agency_id: isSuperAdmin
        ? agencyOptions[0]?.id ?? currentUser?.agency_id ?? 0
        : currentUser?.agency_id ?? 0,
      is_active: true,
    })
    setDialogOpen(true)
  }

  const handleEditUser = (userToEdit: UserSummary) => {
    if (!canManageUsers) return

    setFormMode('edit')
    setSelectedUser(userToEdit)
    reset({
      username: userToEdit.username,
      email: userToEdit.email,
      full_name: userToEdit.full_name ?? '',
      password: '',
      confirm_password: '',
      role_id: userToEdit.role_id,
      agency_id: userToEdit.agency_id,
      is_active: userToEdit.is_active,
    }, { keepDirty: false })
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setSelectedUser(null)
  }

  const onSubmit = async (values: UserFormValues) => {
    if (formMode === 'create') {
      try {
        await createUserMutation.mutateAsync({
        username: values.username.trim(),
        email: values.email.trim(),
        full_name: values.full_name?.trim() || undefined,
        password: values.password ?? '',
        role_id: values.role_id,
        agency_id: values.agency_id,
        })
      } catch (error) {
        // Error handled by mutation onError
      }
      return
    }

    if (!selectedUser) {
      toast.error('No user selected')
      return
    }

    const payload: UpdateUserPayload = {}

    if (values.username.trim() !== selectedUser.username) {
      payload.username = values.username.trim()
    }

    if (values.email.trim() !== selectedUser.email) {
      payload.email = values.email.trim()
    }

    if ((values.full_name ?? '').trim() !== (selectedUser.full_name ?? '')) {
      payload.full_name = values.full_name?.trim() || null
    }

    if (values.role_id !== selectedUser.role_id) {
      payload.role_id = values.role_id
    }

    if (values.is_active !== selectedUser.is_active) {
      payload.is_active = values.is_active
    }

    if (Object.keys(payload).length === 0) {
      toast('No changes detected')
      setDialogOpen(false)
      return
    }

    try {
      await updateUserMutation.mutateAsync({ userId: selectedUser.id, payload })
    } catch (error) {
      // Error handled by mutation onError
    }
  }

  const handleToggleUserStatus = (userToToggle: UserSummary) => {
    if (!canManageUsers) return
    if (userToToggle.id === currentUser?.id) {
      toast.error('You cannot change your own status')
      return
    }

    updateUserMutation.mutate({
      userId: userToToggle.id,
      payload: { is_active: !userToToggle.is_active },
    })
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            User Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage user accounts, roles, and permissions
          </Typography>
        </Box>
        {canManageUsers && (
          <Button
            variant="contained"
            startIcon={<PersonAdd />}
            onClick={handleOpenCreate}
            disabled={rolesQuery.isLoading || agenciesQuery.isLoading}
          >
            Add User
          </Button>
        )}
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Users
              </Typography>
              <Typography variant="h4">
                {usersQuery.isLoading ? <CircularProgress size={24} /> : userStats.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Active Users
              </Typography>
              <Typography variant="h4" color="success.main">
                {usersQuery.isLoading ? <CircularProgress size={24} /> : userStats.active}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Inactive Users
              </Typography>
              <Typography variant="h4" color="error.main">
                {usersQuery.isLoading ? <CircularProgress size={24} /> : userStats.inactive}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Verified Users
              </Typography>
              <Typography variant="h4" color="info.main">
                {usersQuery.isLoading ? <CircularProgress size={24} /> : userStats.verified}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">System Users</Typography>
            {usersQuery.isFetching && <CircularProgress size={20} />}
          </Stack>
          <Divider sx={{ mb: 2 }} />
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Agency</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Last Login</TableCell>
                  {canManageUsers && <TableCell align="right">Actions</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {usersQuery.isLoading && (
                  <TableRow>
                    <TableCell colSpan={canManageUsers ? 6 : 5} align="center">
                      <Box py={4} display="flex" justifyContent="center">
                        <CircularProgress size={32} />
                      </Box>
                    </TableCell>
                  </TableRow>
                )}

                {usersQuery.isError && !usersQuery.isLoading && (
                  <TableRow>
                    <TableCell colSpan={canManageUsers ? 6 : 5} align="center">
                      <Box py={4}>
                        <Typography color="error">Unable to load users</Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}

                {!usersQuery.isLoading && users.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={canManageUsers ? 6 : 5} align="center">
                      <Box py={4}>
                        <People sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                          No users found
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}

                {users.map(userItem => (
                  <TableRow key={userItem.id} hover>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {userItem.full_name || userItem.username}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {userItem.username} • {userItem.email}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {userItem.role ? (
                        <Chip
                          label={getRoleLabel(userItem.role?.name)}
                          color={getRoleColor(userItem.role?.name) as any}
                          size="small"
                        />
                      ) : (
                        <Typography variant="body2">—</Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {userItem.agency?.name || `Agency #${userItem.agency_id}`}
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {userItem.is_active ? (
                          <CheckCircle color="success" fontSize="small" />
                        ) : (
                          <Block color="error" fontSize="small" />
                        )}
                        <Typography
                          variant="body2"
                          color={userItem.is_active ? 'success.main' : 'error.main'}
                        >
                          {userItem.is_active ? 'Active' : 'Inactive'}
                        </Typography>
                        {userItem.is_verified && (
                          <Chip
                            label="Verified"
                            size="small"
                            color="info"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      {userItem.last_login
                        ? new Date(userItem.last_login).toLocaleString()
                        : 'Never'}
                    </TableCell>
                    {canManageUsers && (
                      <TableCell align="right">
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                          <Tooltip title="Toggle active status">
                            <span>
                              <IconButton
                                size="small"
                                color={userItem.is_active ? 'success' : 'default'}
                                onClick={() => handleToggleUserStatus(userItem)}
                                disabled={updateUserMutation.isLoading || userItem.id === currentUser?.id}
                              >
                                {userItem.is_active ? (
                                  <CheckCircle fontSize="small" />
                                ) : (
                                  <Block fontSize="small" />
                                )}
                              </IconButton>
                            </span>
                          </Tooltip>
                          <Tooltip title="Edit user">
                            <span>
                              <IconButton
                                size="small"
                                onClick={() => handleEditUser(userItem)}
                                disabled={rolesQuery.isLoading || agenciesQuery.isLoading}
                              >
                                <Edit fontSize="small" />
                              </IconButton>
                            </span>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit(onSubmit as any)} noValidate>
          <DialogTitle>{formMode === 'create' ? 'Add User' : 'Edit User'}</DialogTitle>
          <DialogContent dividers>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                label="Username"
                fullWidth
                {...register('username')}
                error={Boolean(errors.username)}
                helperText={errors.username?.message}
              />
              <TextField
                label="Email"
                fullWidth
                {...register('email')}
                error={Boolean(errors.email)}
                helperText={errors.email?.message}
              />
              <TextField
                label="Full Name"
                fullWidth
                {...register('full_name')}
                error={Boolean(errors.full_name)}
                helperText={errors.full_name?.message}
              />

              {formMode === 'create' && (
                <>
                  <TextField
                    label="Password"
                    type="password"
                    fullWidth
                    {...register('password')}
                    error={Boolean(errors.password)}
                    helperText={errors.password?.message}
                  />
                  <TextField
                    label="Confirm Password"
                    type="password"
                    fullWidth
                    {...register('confirm_password')}
                    error={Boolean(errors.confirm_password)}
                    helperText={errors.confirm_password?.message}
                  />
                </>
              )}

              <Controller
                name="role_id"
                control={control}
                render={({ field }) => (
                  <TextField
                    select
                    label="Role"
                    fullWidth
                    value={field.value || ''}
                    onChange={event => field.onChange(Number(event.target.value))}
                    error={Boolean(errors.role_id)}
                    helperText={errors.role_id?.message}
                  >
                    {roleOptions.map((role) => (
                      <MenuItem key={role.id} value={role.id}>
                        {getRoleLabel(role.name)}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />

              <Controller
                name="agency_id"
                control={control}
                render={({ field }) => (
                  <TextField
                    select
                    label="Agency"
                    fullWidth
                    value={field.value || ''}
                    onChange={event => field.onChange(Number(event.target.value))}
                    error={Boolean(errors.agency_id)}
                    helperText={errors.agency_id?.message}
                    disabled={!isSuperAdmin}
                  >
                    {agencyOptions.map((agency) => (
                      <MenuItem key={agency.id} value={agency.id}>
                        {agency.name}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />

              {formMode === 'edit' && (
                <Controller
                  name="is_active"
                  control={control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={<Switch checked={field.value} onChange={(_, checked) => field.onChange(checked)} />}
                      label={field.value ? 'Account active' : 'Account inactive'}
                    />
                  )}
                />
              )}
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog} color="secondary" disabled={isSubmitting}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={isSubmitting || createUserMutation.isLoading || updateUserMutation.isLoading}
            >
              {(createUserMutation.isLoading || updateUserMutation.isLoading) && (
                <CircularProgress size={20} sx={{ mr: 1, color: 'inherit' }} />
              )}
              {formMode === 'create' ? 'Create User' : 'Save Changes'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  )
}

export default UsersPage