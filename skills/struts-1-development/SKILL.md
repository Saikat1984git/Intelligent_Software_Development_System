---
name: struts-1-development
description: Use this skill for developing, maintaining, or debugging legacy Apache Struts 1.3 web applications. It provides explicit instructions on Struts 1.3 architecture, the Composable Request Processor, Action classes, ActionForms, tag libraries, XML configuration, standard project structures, and automated dependency injection.
license: MIT
---

# Struts 1.3 Application Development

## Overview
This skill provides the architectural constraints and implementation guidelines for working with Apache Struts 1.3. As the final major release line of the Struts 1 framework, it introduces significant changes from earlier versions, most notably the Chain of Responsibility pattern (Composable Request Processor), the deprecation of `perform()` in favor of `execute()`, and the shift from `ActionError` to `ActionMessage`. Strict adherence to these 1.3-specific paradigms is required.

## Standard Project Structure
Struts 1.3 applications follow a strict Java EE Web Application Archive (WAR) structure. This skill also incorporates a custom script to handle legacy dependency injection without relying on modern build tools. 

When discussing, scaffolding, or executing commands, adhere to this standard layout:

```text
my-struts-1.3-app/
|
├── scripts/
│   └── copy_libs.py                      # Skill script to copy libraries to target
├── src/                                  # Java source files
│   └── com/myapp/
│       ├── action/                       # Action classes (Controllers)
│       ├── form/                         # ActionForm classes
│       └── model/                        # Business logic/DAOs
├── web/                                  # Web root (or WebContent/)
│   ├── META-INF/
│   │   └── context.xml                   # App server context config
│   ├── WEB-INF/
│   │   ├── classes/                      # Compiled .class files and resource bundles
│   │   │   └── MessageResources.properties # i18n and error messages
│   │   ├── lib/                          # Target directory for application dependencies
│   │   ├── struts-config.xml             # Central Struts configuration
│   │   └── web.xml                       # Servlet mapping and deployment descriptor
│   ├── css/
│   ├── images/
│   ├── jsp/                              # Protected JSPs (under WEB-INF/jsp for security)
│   └── index.jsp                         # Landing page, usually forwards to an Action

```

## Instructions

### 0. Dependency Management (The `copy_libs.py` Script)

Because Struts 1.3 is a legacy framework, resolving dependencies via Maven/Gradle can be problematic. This skill uses a static bundle of `.jar` files and an injection script.

* **Action:** Before compiling or deploying a new project environment, you MUST run the `copy_libs.py` script to populate the `WEB-INF/lib` folder.
* **Execution:** `python skills/struts-1-development/scripts/copy_libs.py <destination_path>`
* **Example:** `python skills/struts-1-development/scripts/copy_libs.py "web/WEB-INF/lib"`

### 1. Project Configuration

When setting up or modifying a Struts 1.3 application, manage these primary XML files:

**`web.xml` (Deployment Descriptor):**

* Map the `ActionServlet` (typically to `*.do`).
* Declare the initial parameters for the servlet, pointing to `struts-config.xml`.
* In Struts 1.3, you optionally define `chainConfig` parameters if modifying the default Composable Request Processor chain.

**`struts-config.xml` (Struts Configuration):**

* Must contain elements in this order: `<form-beans>`, `<global-forwards>`, `<action-mappings>`, `<controller>`, `<message-resources>`, `<plug-in>`.
* **Wildcards:** Struts 1.3 supports wildcard mappings. Use them to reduce XML bloat (e.g., `<action path="/edit*" name="{1}Form" type="com.myapp.action.Edit{1}Action">`).

### 2. Implementing ActionForms (The Model/State)

When instructed to create a form for user input:

* Create a Java class extending `org.apache.struts.action.ActionForm`.
* Define properties matching the HTML form fields with standard getters and setters.
* **Validation:** Override `validate(ActionMapping mapping, HttpServletRequest request)`.
* **Struts 1.3 Specifics:** You MUST return an `ActionMessages` object (which replaced `ActionErrors`).
* Use `ActionMessage` for individual errors: `errors.add("username", new ActionMessage("error.username.required"));`. Do NOT use the deprecated `ActionError`.
* **Reset:** Override `reset(ActionMapping mapping, HttpServletRequest request)` to clear boolean/checkbox states before request population.

### 3. Implementing Actions (The Controller)

When instructed to create a controller action:

* Create a Java class extending `org.apache.struts.action.Action` (or `DispatchAction` / `MappingDispatchAction` for grouping related methods).
* **CRITICAL:** Override the `execute()` method. The signature must strictly be:
`public ActionForward execute(ActionMapping mapping, ActionForm form, HttpServletRequest request, HttpServletResponse response) throws Exception`
* *Do NOT* use the `perform()` method. It was deprecated in Struts 1.1 and removed in 1.3.
* Perform business logic within `execute()`. Cast the generic `ActionForm` to your specific form class.
* Return an `ActionForward` object using `mapping.findForward("success")`.
* **Thread Safety:** Action classes are singletons. *Never* use instance variables to store client-specific state. All state must be kept in method-local variables, the request, or the session.

### 4. JSP Views and Custom Tags

When modifying or creating JSP views:

* **URI Taglibs:** Unlike Struts 1.0.2 which required physical `.tld` files, Struts 1.3 resolves tags via URIs directly from the `.jar` files. Use these exact declarations:
`<%@ taglib uri="http://struts.apache.org/tags-html" prefix="html" %>`
`<%@ taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>`
`<%@ taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>`
* Use `<html:form action="/myAction">` (omit the `.do` if the framework is configured to append it, or include it based on `web.xml` conventions).
* Use `<html:text property="fieldName">` to bind inputs.
* Display validation errors using `<html:errors />` or `<html:messages>`.

### 5. Message Resources (I18n and Errors)

* Struts 1.3 relies on a `.properties` file (usually configured as `MessageResources.properties` via the `<message-resources>` tag in `struts-config.xml`).
* Always add keys to this file for UI labels and validation errors (e.g., `error.username.required=Username is a required field.`).

### 6. Legacy Constraints

* **Java Version:** Code should target Java 1.4 or Java 5. While Java 5 introduced Generics and Annotations, Struts 1.3 itself does not natively leverage them in its core API design.
* **Casting:** You will frequently need to cast objects retrieved from the session or request attributes, as well as cast standard `ActionForm` instances to your specific form classes.

### 7. Workflow Execution

When asked to build a Struts 1.3 feature, follow this exact output checklist in your response:

1. **Dependency Check:** Confirm if `copy_libs.py` needs to be executed for the environment.
2. **Model (`ActionForm`):** Provide the Java code, utilizing `ActionMessage` in `validate()`.
3. **Controller (`Action`):** Provide the Java code utilizing the `execute()` method.
4. **View (`.jsp`):** Provide the JSP code using the `http://struts.apache.org/tags-*` URIs.
5. **Resources (`.properties`):** Provide the key-value pairs for `MessageResources.properties`.
6. **Config (`struts-config.xml`):** Provide the exact XML snippets to wire the form and action together.

Exaple Dockerfile for struts 1.3 development environment:
```bash
# Use Tomcat 9 with Java 8
FROM tomcat:9.0-jdk8-corretto

# Remove default Tomcat applications
RUN rm -rf /usr/local/tomcat/webapps/*

# Set working directory
WORKDIR /usr/local/tomcat/webapps/ROOT

# 1. Copy Web Content
COPY WebContent/ .

# 2. Create classes directory
RUN mkdir -p WEB-INF/classes

# 3. Copy Source Code
COPY src/ /tmp/src/

# 4. Compile Java Code (UPDATED LINE BELOW)
# We added ":/usr/local/tomcat/lib/*" to the classpath (-cp) so it finds the Servlet API
RUN find /tmp/src -name "*.java" > sources.txt && \
    javac -cp "WEB-INF/lib/*:/usr/local/tomcat/lib/*" -d WEB-INF/classes @sources.txt && \
    rm sources.txt && \
    rm -rf /tmp/src

# Expose port
EXPOSE 8080

# Start Tomcat
CMD ["catalina.sh", "run"]
```

Example docker compose for struts 1.3 development environment with MySQL database:
```yaml
version: '3.8'

services:
  # The Web Application (Struts)
  app:
    build: .
    ports:
      - "8080:8080"
    depends_on:
      - db
    networks:
      - winlabel-net
    environment:
      # Pass DB info as environment variables (optional, depends on your Java code)
      - DB_HOST=db
      - DB_NAME=winlabel_db
      - DB_USER=root
      - DB_PASS=root

  # The Database (MySQL)
  db:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_DATABASE: winlabel_db
      MYSQL_ROOT_PASSWORD: root
    ports:
      - "3306:3306" # Exposed for local tools like Workbench
    volumes:
      # Persistent storage so data isn't lost on restart
      - db_data:/var/lib/mysql
      # Initialize DB with your existing SQL files
      - ./WebContent/database/schema.sql:/docker-entrypoint-initdb.d/1_schema.sql
      - ./initial_query_statements.sql:/docker-entrypoint-initdb.d/2_data.sql
    networks:
      - winlabel-net

volumes:
  db_data:

networks:
  winlabel-net:
  ```