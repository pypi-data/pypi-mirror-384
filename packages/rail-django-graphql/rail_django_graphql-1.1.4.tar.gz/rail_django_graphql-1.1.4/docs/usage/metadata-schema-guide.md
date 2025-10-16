# Model Metadata Schema Guide

This guide explains how to use the GraphQL model metadata schema to expose Django model information for building rich frontend interfaces with advanced filtering, CRUD operations, and complex forms with nested fields.

## Overview

The metadata schema provides comprehensive information about Django models, including:
- Field definitions with types, constraints, and validation rules
- Relationship mappings (ForeignKey, ManyToMany, OneToOne)
- Permission-based field access control
- Model-level metadata and constraints

This enables frontend applications to:
- Build dynamic tables with advanced filtering
- Generate forms automatically with proper validation
- Create CRUD interfaces with appropriate permissions
- Handle nested relationships and complex data structures

## Configuration

### Enable Metadata Schema

First, enable the metadata schema in your schema settings:

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'default': {
        'schema_settings': {
            'show_metadata': True,  # Enable metadata exposure
            'excluded_apps': [],    # Apps to exclude from metadata
            'excluded_models': [],  # Models to exclude from metadata
        }
    }
}
```

### Security Considerations

The metadata schema respects Django's permission system:
- Only authenticated users can access metadata
- Field-level permissions are enforced
- Model-level permissions are checked
- Sensitive fields can be excluded via settings

## GraphQL Query Structure

### Basic Query

```graphql
query GetModelMetadata {
  modelMetadata(
    appName: "blog"
    modelName: "Post"
    nestedFields: true
    permissionsIncluded: true
  ) {
    appName
    modelName
    verbose_name
    verbose_name_plural
    fields {
      name
      fieldType
      verbose_name
      help_text
      max_length
      null
      blank
      default_value
      choices
      has_permission
    }
    relationships {
      name
      relationshipType
      relatedModel
      relatedApp
      verbose_name
      help_text
      null
      blank
      has_permission
    }
  }
}
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `appName` | String | Yes | Django app name containing the model |
| `modelName` | String | Yes | Name of the Django model |
| `nestedFields` | Boolean | No | Include relationship metadata (default: false) |
| `permissionsIncluded` | Boolean | No | Include permission information (default: false) |

## Response Structure

### ModelMetadata Type

```graphql
type ModelMetadata {
  appName: String!
  modelName: String!
  verbose_name: String
  verbose_name_plural: String
  fields: [FieldMetadata!]!
  relationships: [RelationshipMetadata!]!
}
```

### FieldMetadata Type

```graphql
type FieldMetadata {
  name: String!
  fieldType: String!
  verbose_name: String
  help_text: String
  max_length: Int
  null: Boolean!
  blank: Boolean!
  default_value: String
  choices: [String!]
  has_permission: Boolean!
}
```

### RelationshipMetadata Type

```graphql
type RelationshipMetadata {
  name: String!
  relationshipType: String!
  relatedModel: String!
  relatedApp: String!
  verbose_name: String
  help_text: String
  null: Boolean!
  blank: Boolean!
  has_permission: Boolean!
}
```

## Usage Examples

### Building Dynamic Tables

Use metadata to create dynamic tables with proper column types and filtering:

```javascript
// Frontend JavaScript example
const GET_MODEL_METADATA = gql`
  query GetModelMetadata($appName: String!, $modelName: String!) {
    modelMetadata(
      appName: $appName
      modelName: $modelName
      nestedFields: true
      permissionsIncluded: true
    ) {
      fields {
        name
        fieldType
        verbose_name
        null
        blank
        has_permission
      }
      relationships {
        name
        relationshipType
        relatedModel
        has_permission
      }
    }
  }
`;

// Build table columns from metadata
function buildTableColumns(metadata) {
  const columns = [];
  
  metadata.fields.forEach(field => {
    if (field.has_permission) {
      columns.push({
        key: field.name,
        title: field.verbose_name || field.name,
        dataType: mapGraphQLTypeToTableType(field.fieldType),
        sortable: true,
        filterable: true,
        required: !field.null && !field.blank
      });
    }
  });
  
  metadata.relationships.forEach(rel => {
    if (rel.has_permission) {
      columns.push({
        key: rel.name,
        title: rel.verbose_name || rel.name,
        dataType: 'relationship',
        relatedModel: rel.relatedModel,
        relationshipType: rel.relationshipType
      });
    }
  });
  
  return columns;
}
```

### Generating Forms

Create dynamic forms with proper validation based on field metadata:

```javascript
// Form generation example
function generateFormFields(metadata) {
  const formFields = [];
  
  metadata.fields.forEach(field => {
    if (field.has_permission) {
      const formField = {
        name: field.name,
        label: field.verbose_name || field.name,
        type: mapFieldTypeToInputType(field.fieldType),
        required: !field.null && !field.blank,
        helpText: field.help_text,
        validation: buildValidationRules(field)
      };
      
      // Add specific constraints
      if (field.max_length) {
        formField.maxLength = field.max_length;
      }
      
      if (field.choices && field.choices.length > 0) {
        formField.type = 'select';
        formField.options = field.choices;
      }
      
      formFields.push(formField);
    }
  });
  
  return formFields;
}

function buildValidationRules(field) {
  const rules = [];
  
  if (!field.null && !field.blank) {
    rules.push({ type: 'required', message: `${field.verbose_name} is required` });
  }
  
  if (field.max_length) {
    rules.push({ 
      type: 'maxLength', 
      value: field.max_length,
      message: `Maximum length is ${field.max_length} characters`
    });
  }
  
  // Add type-specific validation
  switch (field.fieldType) {
    case 'EmailField':
      rules.push({ type: 'email', message: 'Please enter a valid email address' });
      break;
    case 'URLField':
      rules.push({ type: 'url', message: 'Please enter a valid URL' });
      break;
    case 'IntegerField':
      rules.push({ type: 'integer', message: 'Please enter a valid integer' });
      break;
  }
  
  return rules;
}
```

### Handling Nested Relationships

Build complex forms with nested relationship fields:

```javascript
// Nested form handling
function buildNestedFormStructure(metadata) {
  const structure = {
    fields: [],
    relationships: []
  };
  
  metadata.relationships.forEach(rel => {
    if (rel.has_permission) {
      const relationshipField = {
        name: rel.name,
        label: rel.verbose_name || rel.name,
        type: rel.relationshipType,
        relatedModel: rel.relatedModel,
        relatedApp: rel.relatedApp,
        required: !rel.null && !rel.blank
      };
      
      // Configure based on relationship type
      switch (rel.relationshipType) {
        case 'ForeignKey':
          relationshipField.inputType = 'select';
          relationshipField.multiple = false;
          break;
        case 'ManyToManyField':
          relationshipField.inputType = 'multiselect';
          relationshipField.multiple = true;
          break;
        case 'OneToOneField':
          relationshipField.inputType = 'select';
          relationshipField.multiple = false;
          break;
      }
      
      structure.relationships.push(relationshipField);
    }
  });
  
  return structure;
}
```

### Advanced Filtering

Create dynamic filter interfaces based on field types:

```javascript
// Filter generation
function generateFilterOptions(metadata) {
  const filters = [];
  
  metadata.fields.forEach(field => {
    if (field.has_permission) {
      const filter = {
        field: field.name,
        label: field.verbose_name || field.name,
        operators: getOperatorsForFieldType(field.fieldType)
      };
      
      // Add field-specific filter options
      if (field.choices && field.choices.length > 0) {
        filter.type = 'select';
        filter.options = field.choices;
        filter.operators = ['exact', 'in'];
      } else {
        filter.type = getFilterTypeForField(field.fieldType);
      }
      
      filters.push(filter);
    }
  });
  
  return filters;
}

function getOperatorsForFieldType(fieldType) {
  const operatorMap = {
    'CharField': ['exact', 'icontains', 'startswith', 'endswith'],
    'TextField': ['exact', 'icontains', 'startswith', 'endswith'],
    'IntegerField': ['exact', 'lt', 'lte', 'gt', 'gte', 'range'],
    'FloatField': ['exact', 'lt', 'lte', 'gt', 'gte', 'range'],
    'DateField': ['exact', 'lt', 'lte', 'gt', 'gte', 'range'],
    'DateTimeField': ['exact', 'lt', 'lte', 'gt', 'gte', 'range'],
    'BooleanField': ['exact'],
    'EmailField': ['exact', 'icontains'],
    'URLField': ['exact', 'icontains']
  };
  
  return operatorMap[fieldType] || ['exact'];
}
```

## Integration with Existing Schema

The metadata schema integrates seamlessly with your existing GraphQL schema:

```python
# In your Django GraphQL setup
from rail_django_graphql.extensions import ModelMetadataQuery

class Query(ModelMetadataQuery, graphene.ObjectType):
    # Your existing queries
    all_posts = graphene.List(PostType)
    
    def resolve_all_posts(self, info):
        return Post.objects.all()

schema = graphene.Schema(query=Query)
```

## Permission System Integration

The metadata schema respects Django's permission system:

### Model-Level Permissions

```python
# models.py
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    class Meta:
        permissions = [
            ('view_post_title', 'Can view post title'),
            ('view_post_content', 'Can view post content'),
        ]
```

### Field-Level Permission Checking

The system automatically checks for field-specific permissions:
- `view_{app}_{model}_{field}` - Permission to view specific field
- `change_{app}_{model}_{field}` - Permission to modify specific field

### Custom Permission Logic

You can extend the permission checking logic:

```python
# Custom permission checker
from rail_django_graphql.extensions.metadata import ModelMetadataExtractor

class CustomMetadataExtractor(ModelMetadataExtractor):
    def _check_field_permission(self, field, user, model):
        # Custom permission logic
        if field.name == 'sensitive_field':
            return user.has_perm('app.view_sensitive_data')
        
        return super()._check_field_permission(field, user, model)
```

## Error Handling

The metadata schema handles various error conditions gracefully:

### Common Error Scenarios

1. **Model Not Found**: Returns `null` when model doesn't exist
2. **No Permission**: Returns `null` when user lacks access
3. **Metadata Disabled**: Returns `null` when `show_metadata` is `False`
4. **Invalid Parameters**: GraphQL validation handles invalid inputs

### Error Response Example

```graphql
{
  "data": {
    "modelMetadata": null
  },
  "errors": [
    {
      "message": "Model 'InvalidModel' not found in app 'blog'",
      "path": ["modelMetadata"]
    }
  ]
}
```

## Performance Considerations

### Caching

Consider caching metadata responses for better performance:

```python
# Django cache example
from django.core.cache import cache

def get_cached_metadata(app_name, model_name, user_id):
    cache_key = f"metadata:{app_name}:{model_name}:{user_id}"
    return cache.get(cache_key)

def set_cached_metadata(app_name, model_name, user_id, metadata):
    cache_key = f"metadata:{app_name}:{model_name}:{user_id}"
    cache.set(cache_key, metadata, timeout=3600)  # 1 hour
```

### Selective Field Loading

Use the `nestedFields` and `permissionsIncluded` parameters to control response size:

```graphql
# Minimal metadata for simple use cases
query GetBasicMetadata {
  modelMetadata(
    appName: "blog"
    modelName: "Post"
    nestedFields: false
    permissionsIncluded: false
  ) {
    fields {
      name
      fieldType
      null
      blank
    }
  }
}
```

## Best Practices

1. **Security First**: Always enable permission checking in production
2. **Cache Responses**: Cache metadata to improve performance
3. **Selective Loading**: Only request needed metadata fields
4. **Error Handling**: Implement proper error handling in frontend
5. **Documentation**: Document custom field types and relationships
6. **Testing**: Test metadata exposure with different user permissions

## Troubleshooting

### Common Issues

1. **Metadata Not Showing**: Check `show_metadata` setting
2. **Permission Denied**: Verify user has appropriate permissions
3. **Missing Fields**: Check if fields are excluded in settings
4. **Performance Issues**: Implement caching and selective loading

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'rail_django_graphql.extensions.metadata': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

This comprehensive guide should help you implement and use the metadata schema effectively for building rich frontend interfaces with Django GraphQL.