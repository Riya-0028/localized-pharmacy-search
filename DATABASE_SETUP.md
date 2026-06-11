# Database Setup Instructions

## Required Database Changes for Pharmacy License Verification

Your application now requires additional fields in the `pharmacy` table to support the license verification and approval system. Follow these steps to update your database:

### Step 1: Add Missing Columns to Pharmacy Table

Run the following SQL commands to add the required columns:

```sql
-- Add license_number column
ALTER TABLE pharmacy ADD COLUMN license_number VARCHAR(100) NOT NULL UNIQUE;

-- Add approval_status column (values: pending, approved, rejected)
ALTER TABLE pharmacy ADD COLUMN approval_status VARCHAR(20) DEFAULT 'pending';

-- Add registered_date column
ALTER TABLE pharmacy ADD COLUMN registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
```

### Step 2: Update Existing Records (Optional)

If you have existing pharmacy records, you may need to add default values:

```sql
-- For existing records without license_number, use a placeholder
UPDATE pharmacy SET license_number = CONCAT('LIC_', username) WHERE license_number IS NULL OR license_number = '';

-- Set all existing records to 'approved' status
UPDATE pharmacy SET approval_status = 'approved';
```

### Step 3: Create Admin Approval System (Optional - Coming Soon)

In the future, you may want to create an admin dashboard to approve/reject registrations. You can create an admin panel route that allows viewing pending pharmacies:

```sql
-- Query to view pending registrations
SELECT id, name, address, contact, license_number, registered_date 
FROM pharmacy 
WHERE approval_status = 'pending' 
ORDER BY registered_date DESC;
```

## New Features Implemented

✅ **Pharmacy Registration Form**
- Now includes Pharmacy License Number field
- Validates 10-digit phone numbers
- Better form styling with error handling

✅ **License Verification System**
- Registrations start with "pending" status
- Admin must approve before pharmacy can login
- Users see clear messages about approval status

✅ **Enhanced UI**
- Navigation bar at top with quick action buttons
- Emergency search button in top right
- Login and Register Pharmacy buttons in top right
- Professional dashboard design
- Responsive layout for mobile devices

✅ **New Pages**
- Pharmacy Registration Pending (shows after registration)
- Pharmacy Dashboard (placeholder for future features)
- Enhanced Pharmacy Login with error messages

## Testing the New Workflow

1. Visit the welcome page: `http://localhost:5000/`
2. Click "Register Pharmacy" button in top right
3. Fill in the registration form including the license number
4. You'll be redirected to a "pending approval" page
5. To test login with approval:
   - Manually update the pharmacy record in the database:
     ```sql
     UPDATE pharmacy SET approval_status = 'approved' WHERE username = 'your_username';
     ```
6. Now you can log in with your credentials

## Next Steps

Consider implementing:
- Admin panel to approve/reject pharmacies
- Email notifications for approval status
- Enhanced pharmacy dashboard for inventory management
- Medicine search integration
