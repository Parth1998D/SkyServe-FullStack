# main.py
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from pathlib import Path
from uuid import uuid4
import shutil

# Load environment variables
load_dotenv()

# Create necessary directories
os.makedirs("uploads", exist_ok=True)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-development-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# Database setup
# For development, we'll use SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with echo=True for SQL logging
engine = create_engine(
    DATABASE_URL,
    echo=True,  # This will log all SQL statements
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database Models
class User(Base):
    """User model for storing user authentication and profile data"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    datasets = relationship("Dataset", back_populates="owner", cascade="all, delete-orphan")
    shapes = relationship("Shape", back_populates="owner", cascade="all, delete-orphan")

class Dataset(Base):
    """Dataset model for storing uploaded map files"""
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    file_path = Column(String)
    file_type = Column(String)  # 'geojson', 'kml', or 'tiff'
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="datasets")

class DatasetResponse(BaseModel):
    id: int
    name: str
    file_type: str
    owner_id: int

    class Config:
        orm_mode = True

class Shape(Base):
    """Shape model for storing custom drawn shapes on the map"""
    __tablename__ = "shapes"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)  # Will store "Feature"
    geometry = Column(JSON)  # Will store the geometry object
    properties = Column(JSON, default={})
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="shapes")

class ShapeResponse(BaseModel):
    id: int
    type: Optional[str]
    geometry: dict
    properties: dict
    owner_id: int

    class Config:
        orm_mode = True

class ShapeUpdate(BaseModel):
    geometry: dict
    properties: dict
    type: Optional[str]

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DatasetCreate(BaseModel):
    name: str

class ShapeCreate(BaseModel):
    geometry: dict
    properties: dict
    type: Optional[str]


def validate_file_type(filename: str) -> str:
    """Validate and return the file type"""
    allowed_extensions = {
        '.geojson': 'geojson',
        '.json': 'geojson',
        '.kml': 'kml',
        '.tiff': 'tiff',
        '.tif': 'tiff'
    }
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="File type not supported. Allowed types: .geojson, .kml, .tiff, .tif"
        )
    return allowed_extensions[suffix]


def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """Save uploaded file to destination"""
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()

# Initialize FastAPI app
app = FastAPI(
    title="Map Application API",
    description="API for managing map users, shapes, and datasets",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication functions
def verify_password(plain_password, hashed_password):
    """Verify password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# API Endpoints
@app.post("/users", response_model=Token, summary="Create new user")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create new user with email and password
    Returns JWT access token
    """
    try:
        # Check if user exists
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = User(email=user.email, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/shapes", response_model=List[ShapeResponse], summary="Get all shapes")
async def get_shapes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all shapes belonging to the current user
    """
    shapes = db.query(Shape).filter(Shape.owner_id == current_user.id).all()
    return shapes

@app.post("/shapes", response_model=ShapeResponse, summary="Create new shape")
async def create_shape(
    shape: ShapeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new shape for the current user
    """
    try:
        shape_data = shape.dict()
        if 'id' in shape_data:
            del shape_data['id']
            
        db_shape = Shape(
            **shape_data,
            owner_id=current_user.id
        )
        db.add(db_shape)
        db.commit()
        db.refresh(db_shape)
        return db_shape
    except Exception as e:
        print(f"Error creating shape: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/shapes/{shape_id}", response_model=ShapeResponse, summary="Update shape")
async def update_shape(
    shape_id: int,
    shape: ShapeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing shape
    """
    db_shape = db.query(Shape).filter(
        Shape.id == shape_id,
        Shape.owner_id == current_user.id
    ).first()
    
    if not db_shape:
        raise HTTPException(status_code=404, detail="Shape not found")
    
    try:
        db_shape.geometry = shape.geometry
        db_shape.properties = shape.properties
        db_shape.type = shape.type
        db.commit()
        db.refresh(db_shape)
        return db_shape
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/shapes/{shape_id}", summary="Delete shape")
async def delete_shape(
    shape_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a shape
    """
    db_shape = db.query(Shape).filter(
        Shape.id == shape_id,
        Shape.owner_id == current_user.id
    ).first()
    
    if not db_shape:
        raise HTTPException(status_code=404, detail="Shape not found")
    
    try:
        db.delete(db_shape)
        db.commit()
        return {"message": "Shape deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# @app.delete("/shapes", summary="Delete multiple shapes")
# async def delete_multiple_shapes(
#     shape_ids: List[int],
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Delete multiple shapes at once
#     """
#     try:
#         result = db.query(Shape).filter(
#             Shape.id.in_(shape_ids),
#             Shape.owner_id == current_user.id
#         ).delete(synchronize_session=False)
        
#         db.commit()
#         return {"message": f"{result} shapes deleted successfully"}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/datasets", response_model=DatasetResponse, summary="Upload new dataset")
async def upload_dataset(
    name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a new dataset (GeoJSON, KML, or TIFF file)
    """
    try:
        # Validate file type
        file_type = validate_file_type(file.filename)
        
        # Generate unique filename
        unique_filename = f"{uuid4()}{Path(file.filename).suffix}"
        file_path = Path("uploads") / unique_filename
        
        # Save file
        save_upload_file(file, file_path)
        
        # Create dataset record
        dataset = Dataset(
            name=name,
            file_path=str(file_path),
            file_type=file_type,
            owner_id=current_user.id
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        return dataset
    
    except Exception as e:
        # Clean up file if saved
        print(f"Error creating shape: {e}")
        if 'file_path' in locals():
            Path(file_path).unlink(missing_ok=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/datasets", response_model=List[DatasetResponse], summary="List all datasets")
async def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all datasets belonging to the current user
    """
    datasets = db.query(Dataset).filter(Dataset.owner_id == current_user.id).all()
    return datasets

@app.get("/datasets/{dataset_id}", response_model=DatasetResponse, summary="Get dataset details")
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific dataset
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.owner_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return dataset

@app.get("/datasets/{dataset_id}/download", summary="Download dataset file")
async def download_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download the file for a specific dataset
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.owner_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    file_path = Path(dataset.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=f"{dataset.name}{file_path.suffix}",
        media_type="application/octet-stream"
    )

@app.delete("/datasets/{dataset_id}", summary="Delete dataset")
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a dataset and its associated file
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.owner_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Delete file
        file_path = Path(dataset.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete database record
        db.delete(dataset)
        db.commit()
        
        return {"message": "Dataset deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Initialize database
def init_db():
    """Initialize the database"""
    Base.metadata.create_all(bind=engine)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run startup events"""
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)