from typing import List, Tuple, Optional
from sqlalchemy import select, func, or_, update
from sqlalchemy.orm import Session, joinedload

from app.models.user import User, UserRole, AuthSession
from app.models.employee import Employee, EmployeeProfile
from app.models.department import Department
from app.models.activity import ActivityLog
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.core.security import hash_password
from app.core.exceptions import NotFoundError, ConflictError


class EmployeeService:
    """Service handling employee lifecycle, directory lookups, and account activation."""

    @staticmethod
    def _generate_next_employee_code(db: Session) -> str:
        """Generate auto-incrementing JT-xxx employee identifier."""
        stmt = select(Employee.employee_id)
        existing_codes = db.execute(stmt).scalars().all()
        max_num = 0
        for code in existing_codes:
            if code and code.startswith("JT-"):
                num_part = code[3:]
                if num_part.isdigit():
                    max_num = max(max_num, int(num_part))
        next_num = max_num + 1
        return f"JT-{next_num:03d}"

    @classmethod
    def create_employee(
        cls,
        db: Session,
        data: EmployeeCreate,
        founder_user: User,
    ) -> Employee:
        """Create User account and linked Employee record within a single transaction."""
        # Check email conflict
        existing = db.execute(select(User).where(User.email == data.email)).scalar_one_or_none()
        if existing:
            raise ConflictError(f"User with email '{data.email}' already exists")

        if data.phone:
            existing_phone = db.execute(select(User).where(User.phone == data.phone)).scalar_one_or_none()
            if existing_phone:
                raise ConflictError(f"User with phone '{data.phone}' already exists")

        # Validate department if provided
        if data.department_id:
            dept = db.execute(
                select(Department).where(
                    Department.id == data.department_id,
                    Department.is_active.is_(True),
                )
            ).scalar_one_or_none()
            if not dept:
                raise NotFoundError(f"Department '{data.department_id}' not found")

        # Create user
        user = User(
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=UserRole.employee,
            is_active=True,
            email_verified=True,
            phone_verified=bool(data.phone),
        )
        db.add(user)
        db.flush()

        # Generate JT-xxx code
        emp_code = cls._generate_next_employee_code(db)

        employee = Employee(
            user_id=user.id,
            employee_id=emp_code,
            full_name=data.full_name,
            department_id=data.department_id,
            designation=data.designation,
            joining_date=data.joining_date,
            is_active=True,
            created_by=founder_user.id,
        )
        db.add(employee)
        db.flush()

        # Initialize profile
        profile = EmployeeProfile(
            employee_id=employee.id,
        )
        db.add(profile)
        db.add(
            ActivityLog(
                user_id=founder_user.id,
                employee_id=employee.id,
                event_type="employee_created",
                event_data={"employee_name": employee.full_name},
            )
        )
        db.commit()

        # Reload with relationships
        return cls.get_employee(db, employee.id)

    @staticmethod
    def list_employees(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        department_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Employee], int]:
        """Query paginated employee directory with filtering and search."""
        query = (
            select(Employee)
            .join(Employee.user)
            .outerjoin(Employee.department)
            .options(joinedload(Employee.user), joinedload(Employee.department))
        )
        count_query = select(func.count(Employee.id)).join(Employee.user)

        # Filters
        if is_active is not None:
            query = query.where(Employee.is_active == is_active)
            count_query = count_query.where(Employee.is_active == is_active)

        if department_id:
            query = query.where(Employee.department_id == department_id)
            count_query = count_query.where(Employee.department_id == department_id)

        if search:
            search_pattern = f"%{search.strip()}%"
            search_cond = or_(
                Employee.full_name.ilike(search_pattern),
                Employee.employee_id.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
            query = query.where(search_cond)
            count_query = count_query.where(search_cond)

        total = db.execute(count_query).scalar() or 0
        offset = max(0, (page - 1) * page_size)
        items = db.execute(query.order_by(Employee.created_at.desc()).offset(offset).limit(page_size)).scalars().all()

        return list(items), total

    @staticmethod
    def get_employee(db: Session, employee_id: str) -> Employee:
        """Fetch employee by UUID or JT-xxx code, raising NotFoundError if absent."""
        stmt = (
            select(Employee)
            .where(or_(Employee.id == employee_id, Employee.employee_id == employee_id))
            .options(joinedload(Employee.user), joinedload(Employee.department))
        )
        emp = db.execute(stmt).scalar_one_or_none()
        if not emp:
            raise NotFoundError(f"Employee '{employee_id}' not found")
        return emp

    @staticmethod
    def get_employee_by_user_id(db: Session, user_id: str) -> Employee:
        """Retrieve Employee associated with a specific User ID."""
        stmt = (
            select(Employee)
            .where(Employee.user_id == user_id)
            .options(joinedload(Employee.user), joinedload(Employee.department))
        )
        emp = db.execute(stmt).scalar_one_or_none()
        if not emp:
            raise NotFoundError(f"Employee record for user '{user_id}' not found")
        return emp

    @classmethod
    def update_employee(
        cls,
        db: Session,
        employee_id: str,
        data: EmployeeUpdate,
    ) -> Employee:
        """Update employee details."""
        emp = cls.get_employee(db, employee_id)

        if data.full_name is not None:
            emp.full_name = data.full_name
        if data.department_id is not None:
            if data.department_id:
                dept = db.execute(
                    select(Department).where(
                        Department.id == data.department_id,
                        Department.is_active.is_(True),
                    )
                ).scalar_one_or_none()
                if not dept:
                    raise NotFoundError(f"Department '{data.department_id}' not found")
            emp.department_id = data.department_id or None
        if data.designation is not None:
            emp.designation = data.designation
        if data.joining_date is not None:
            emp.joining_date = data.joining_date
        if data.profile_photo_url is not None:
            emp.profile_photo_url = data.profile_photo_url

        if data.phone is not None:
            emp.user.phone = data.phone

        db.commit()
        db.refresh(emp)
        return emp

    @classmethod
    def update_employee_status(
        cls,
        db: Session,
        employee_id: str,
        is_active: bool,
    ) -> Employee:
        """Activate or deactivate an employee and cascade to user login status."""
        emp = cls.get_employee(db, employee_id)
        emp.is_active = is_active
        emp.user.is_active = is_active
        db.commit()
        db.refresh(emp)
        return emp

    @classmethod
    def reset_employee_password(
        cls,
        db: Session,
        employee_id: str,
        new_password: str,
        founder_user: User,
    ) -> None:
        """Set a new employee password and revoke saved refresh sessions."""
        employee = cls.get_employee(db, employee_id)
        employee.user.password_hash = hash_password(new_password)
        db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == employee.user_id)
            .values(is_revoked=True)
        )
        db.add(
            ActivityLog(
                user_id=founder_user.id,
                employee_id=employee.id,
                event_type="employee_password_reset",
                event_data={"employee_id": employee.employee_id},
            )
        )
        db.commit()
