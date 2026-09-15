# RBAC Matrix

| Operation | Admin | Manager | Employee |
|---|---:|---:|---:|
| View dashboard | Yes | Yes | Yes |
| Manage users (create / delete) | Yes | No | No |
| Reset another user's password | Yes | No | No |
| Create/update/delete products | Yes | Yes | No |
| Read products | Yes | Yes | Yes |
| Create customers | Yes | Yes | Yes |
| Update/delete customers | Yes | Yes | No |
| Adjust inventory | Yes | Yes | No |
| Create sales | Yes | Yes | Yes |
| Read own employee sales | Yes | Yes | Yes |
| Read all sales | Yes | Yes | No |
| View audit log (/audit/) | Yes | No | No |
| Manage own profile (password, TOTP 2FA) | Yes | Yes | Yes |

Notes:
- Every page/action is protected server-side with `role_required(...)` + `login_required`.
- Cannot delete yourself; password reset is allowed for any other account and also
  clears an active lockout.