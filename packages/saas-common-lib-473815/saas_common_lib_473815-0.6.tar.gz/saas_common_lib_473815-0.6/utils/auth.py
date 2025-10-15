from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from models.saas_context import SaasContext, saasContext
from models.user_model import PageDefinitionModel
from entity.user_entity import PageDefinition
from entity.inventory_entity import CategoryEntity
from database.postgres import get_db
from sqlalchemy.orm import Session

SECRET_KEY = "nsn"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



def verify_token(req: Request = None, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        print ("token - ", token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print ("Payload - ", payload)

        client_id = payload.get("client_id")

        path = req.url.path
        path_parts = path.split("/")
        url_client_id = path_parts[2]
        url_module = path_parts[3]
        url_operation = path_parts[4]
        roles = payload["roles"]
        grants = payload["grants"]
        realm = payload["realm"]


        if grants.index(realm) < 0 :
            raise HTTPException(status_code=403, detail="Restricted Grant. Please contact administrator.")

      
        #assigning default realm and client_id at the framework level
        default_realm = "realm"
        default_client_id = "saas"
        records = db.query(CategoryEntity).filter(CategoryEntity.client_id == default_client_id).order_by(CategoryEntity.slug).all()

        print("records - ",records)
        models = CategoryEntity.copyToModels(records)
        
        print("models - ", models)
        lookup = {cat.id: cat for cat in models}
        default_category = lookup.get(default_realm)

        if default_category :
            if default_category.sub_categories.index(realm) >= 0 :
                realm_category = lookup.get(realm)
                print("realm_category - ", realm_category)
                if realm_category.sub_categories.index(url_module) >= 0 :
                    access_category = lookup.get(url_module)
                    print("access_category - ", access_category)
                    if access_category.sub_categories.index(url_operation) >= 0 :
                        page_definitions = get_page_definition(roles, url_module, client_id, db)
                        pageDefinitionModels = PageDefinition.copyToModels(page_definitions)
                        print("pageDefinitionModels - ", pageDefinitionModels)
                        screenId = get_screen_id(pageDefinitionModels, url_operation)
                        print ("screen_id - ", screenId)
            
                        if (screenId == "accessRestricted"):
                            raise HTTPException(status_code=403, detail="Restricted Access. Please contact administrator.")

                        context = SaasContext(client_id, url_module, url_operation, str(payload.get("user_id")), roles, grants, screenId)
                        saasContext.set(context)
                    if context is None:
                        raise HTTPException(status_code=403, detail="Restricted Access. Please contact administrator.")
                    return context
                else :
                    raise HTTPException(status_code=403, detail="Restricted Access. Please contact administrator.")
            else :
                print(f"User do not have access to ", url_module)
                raise HTTPException(status_code=403, detail="Restricted Grants. Please contact administrator.")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        print(f"Other JWT error: {e}")
        raise HTTPException(status_code=401, detail="Invalid Token")
    except ValueError:
        print(f"User do not have access to ", url_module)
        raise HTTPException(status_code=403, detail="Restricted Grants. Please contact administrator.")


def get_screen_id(page_definitions, url_operation):    
    for page_def in page_definitions:
        if "ALL" in page_def.operations:
            return page_def.screen_id
        if url_operation in page_def.operations and page_def.load_type == "include":
            return page_def.screen_id
        if url_operation not in page_def.operations and page_def.load_type == "exclude":
            return page_def.screen_id
    return "accessRestricted"


def get_page_definition(roles: list[str], module: str, client_id: str, db: Session):
    page_definitions = db.query(PageDefinition).filter(
                            PageDefinition.role.in_(roles),  # Multiple roles
                            PageDefinition.module == module,  # Matching module
                            PageDefinition.client_id == client_id  # Matching client ID
                        ).all()

    return page_definitions  # Returning the fetched results
