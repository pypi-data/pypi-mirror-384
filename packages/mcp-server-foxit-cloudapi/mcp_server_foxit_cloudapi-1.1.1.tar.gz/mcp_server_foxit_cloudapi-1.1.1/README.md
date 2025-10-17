# MCP server for using the Foxit Cloud API

## Requirements

- 本地需要安装python包管理器 [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Features
- PDF创建和转换：支持从其他文件格式创建PDF文件，并将PDF转换为其他格式，如HTML、Word等。
- PDF合并和拆分：支持将多个PDF文件合并为一个，或将一个PDF文件拆分为多个。
- PDF压缩和优化：通过图像压缩和优化来减小PDF文件大小，扁平化，线性化文档等功能
- PDF安全：提供密码保护和高级加密功能，确保PDF文件的安全性。

## Tools

### combine_pdf

将压缩或归档文件中的多个PDF文档，合并为一个PDF文档。使用示例1：把<absolute_path/file_name.zip>中的PDF文档合并为一个PDF。使用示例2：把<url/file_name.pdf>, <url/file_name1.pdf>合并为一个PDF。

参数：
  - path: string - 压缩或归档文件的绝对路径或多个URL地址
  - config: object - 配置项
    - isAddBookmark: boolean - 是否添加书签
    - isAddTOC: boolean - 是否添加目录
    - isContinueMerge: boolean - 如果发生错误是否继续合并
    - isRetainPageNum: boolean - 是否保留页面逻辑号
    - bookmarkLevels: enum('0', '1', '2', '3', '4', '5') - 是否显示目录的等级

### compare_pdf

逐页比较一个PDF文档（作为“基准文档”）与另一个PDF文档（作为“比较文档”）。使用示例1：把<absolute_path/file_name.pdf>与<absolute_path/file_name.pdf>进行比较。使用示例2：把<absolute_path/file_name.pdf>与<absolute_path/file_name.pdf>进行比较，比较结果为：pdf。使用示例3：把<url/file_name.pdf>与<url/file_name.pdf>进行比较。

参数：
  - basePath: string - 基准PDF文档的绝对路径或URL地址
  - comparePath: string - 比较PDF文档的绝对路径或URL地址
  - resultType: enum('json', 'pdf') - 结果类型
  - compareType: enum('all', 'text') - 比较类型

### compress_pdf

使用指定的压缩级别压缩PDF文档。使用示例1：压缩<absolute_path/file_name.pdf>。使用示例2：压缩<absolute_path/file_name.pdf>，压缩级别为：high。使用示例3：压缩<url/file_name.pdf>。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - compressionLevel: enum('low', 'medium', 'high') - 压缩级别

### convert_pdf

转换PDF文档到其他格式，支持格式：word, excel, ppt, image, text, html。使用示例1：把<absolute_path/file_name.pdf>转换为word。使用示例2：把<absolute_path/file_name.pdf>转换为text。使用示例3：把<url/file_name.pdf>转换为excel。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - format: enum('word', 'excel', 'ppt', 'image', 'text', 'html') - 转换后的文件类型

### create_pdf

从其他格式，创建或转换为PDF文档，支持格式：word，excel，ppt，image，text。使用示例1：把<absolute_path/file_name.docx>转换为PDF。使用示例2：把<absolute_path/file_name.txt>转换为PDF。使用示例3：把<url/file_name.png>转换为PDF。

参数：
  - path: string - 转换文件的绝对路径或URL地址
  - format: enum('word', 'excel', 'ppt', 'image', 'text') - 输入的文件类型

### create_pdf_from_html

从HTML文件或指定站点URL创建PDF。使用示例1：把<absolute_path/file_name.html>转换为PDF。使用示例2：把\<url>转换为PDF。使用示例3：把\<url>转换为PDF，页面模式为：单页。使用示例4：把<url/flie_name.html>转换为PDF，输入格式为：html。

参数：
  - format: enum('url', 'html', 'htm', 'shtml') - 输入格式，如果是url，则url参数不能为空，否则path参数不能为空
  - path: string - HTML文件的绝对路径或URL地址
  - url: string - URL
  - config: object - 配置项
    - width: number - 页面宽度，该值必须大于16，默认值为900(单位为1/72英寸)
    - height: number - 页面高度，该值必须大于16，默认值为600(单位为1/72英寸)
    - rotate: number - 页面旋转，0：0度，1：90度，2：180度，3：270度
    - pageMode: number - 页面模式，0：单页，1：多页
    - pageScaling: number - 页面缩放，1：适应页面，2：适应内容

### extract_pdf

提取PDF文档中的文本或图像。使用示例1：提取<absolute_path/file_name.pdf>中的文本。使用示例2：提取<absolute_path/file_name.pdf>中的图片。使用示例3：提取<url/file_name.pdf>中的文本。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - mode: enum('extractImages', 'extractText') - 提取模式，extractText表示提取文本，extractImages表示提取图片
  - pageRange: string - 提取页面范围，A、B和C以逗号分隔。A、B或C可以取数字，如99，也可以取范围，如1-30。如果为空，则提取整个文档

### flatten_pdf

使PDF文档页面扁平化，使注释和表单字段成为页面内容的一部分。使用示例1：把<absolute_path/file_name.pdf>扁平化。使用示例2：把<url/file_name.pdf>扁平化。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - pageRange: string - PDF文档的页面范围。文档中的页面可以按任何顺序引用，从开始或结束都可以。例如：1、2、3、7-9、all。如果未指定，则执行所有页面

### linearize_pdf

线性化PDF文档。使用示例1：把<absolute_path/file_name.pdf>线性化。使用示例2：把<url/file_name.pdf>线性化。

参数：
  - path: string - PDF文档的绝对路径或URL地址

### manipulation_pdf

操作PDF文档，例如删除页面，旋转页面，移动页面。使用示例1：删除<absolute_path/file_name.pdf>的第1页。使用示例2：把<absolute_path/file_name.pdf>的第2页移到第1页。使用示例3：删除<url/file_name.pdf>的第1页。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - config: object - PDF文档操作配置
    - pageAction: enum('delete', 'rotate', 'move') - 页面操作类型
    - pages: array(number) - 操作的页码，如[0,1,2,3]，页面索引从0开始
    - angle: number - 页面旋转，0：0度，1：90度，2：180度，-1：270度
    - destination: number - 目标页码，如果"页面操作类型"是"移动"，它是必需的

### protect_pdf

使用用户或/和所有者密码保护PDF文档，并对某些功能设置限制。使用示例1：给<absolute_path/file_name.pdf>设置用户密码，密码为：123456。使用示例2：给<absolute_path/file_name.pdf>设置所有者密码，密码为：123456，权限设置为：不允许修改PDF内容。使用示例3：给<url/file_name.pdf>设置用户密码，密码为：123456。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - passwordProtection: object - 密码保护设置，必须至少设置一个密码
    - userPassword: string - 用户密码
    - ownerPassword: string - 所有者密码
  - permission: object - 权限设置
    - PRINT_LOW_QUALITY: boolean - 以正常模式打印PDF文档
    - PRINT_HIGH_QUALITY: boolean - 以高质量打印PDF文档
    - EDIT_CONTENT: boolean - 修改PDF内容。设置该值后，用户可以通过操作修改PDF文档的内容
    - EDIT_FILL_AND_SIGN_FORM_FIELDS: boolean - 填写PDF表格。如果设置了该值，用户可以填写交互式表单字段（包括签名字段）
    - EDIT_ANNOTATION: boolean - 操作文本注释和填写交互式表单字段。如果还设置了"修改PDF内容"值，则用户可以创建或修改交互式表单字段
    - EDIT_DOCUMENT_ASSEMBLY: boolean - 组装PDF文档。如果设置了这个值，就可以组装文档（插入、旋转或删除页面以及创建书签或缩略图），而不管是否设置了"修改PDF内容"值
    - COPY_CONTENT: boolean - 残疾的支持。如果设置了此值，用户可以提取文本和图形，以支持残疾用户的可访问性或用于其他目的
  - encryptionAlgorithm: enum('AES_128', 'AES_256', 'RC4') - 加密算法

### remove_password

从PDF文档中删除密码安全性。使用示例1：移除<absolute_path/file_name.pdf>的用户密码，密码为：123456。使用示例2：移除<absolute_path/file_name.pdf>的所有者密码，密码为：123456。使用示例3：移除<url/file_name.pdf>的用户密码，密码为：123456。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - password: string - PDF文档密码。如果PDF受所有者密码保护，则用户需要在该字段中使用所有者密码来取消文档安全性，否则用户需要传入用户密码来打开文档

### split_pdf

将PDF文档拆分为多个较小的文档。使用示例1：把<absolute_path/file_name.pdf>拆分为多个文档，拆分后的页数为：3。使用示例2：把<url/file_name.pdf>拆分为多个文档，拆分后的页数为：2。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - config: object - 配置项
    - pageCount: number - 拆分后的页数

### apply_certificate

申请数字证书，返回证书ID。使用示例1：申请数字证书，经办人：<agent_name>，身份证号码：<agent_id_card>，手机号码：<agent_phone>，企业名称：<org_name>，企业法定代表人：<org_legal_person>，企业统一社会信用代码：<org_register_no>，法人证件号：<org_legal_person_id_card>。使用示例2：申请数字证书，经办人：<agent_name>，身份证号码：<agent_id_card>，手机号码：<agent_phone>，企业名称：<org_name>，企业法定代表人：<org_legal_person>，企业统一社会信用代码：<org_register_no>，法人证件号：<org_legal_person_id_card>。再对<url/file_name.pdf>进行数字签名。

参数：
  - certValid: number - 证书有效期，单位为年。最长5年，最短1年。默认值为1年
  - agentName: string - 经办人名称
  - agentIdCard: string - 经办人身份证号码
  - agentPhone: string - 经办人手机号码
  - orgName: string - 企业组织名称
  - orgLegalPerson: string - 企业组织法定代表人
  - orgRegisterNo: string - 企业统一社会信用代码
  - orgLegalPersonIdCard: string - 法人证件号

返回：证书ID（后续 sign_pdf 使用）

### sign_pdf

对PDF文档进行数字签名。使用示例1：对<absolute_path/file_name.pdf>进行数字签名，证书ID为：<cert_id>。使用示例2：申请数字证书，经办人：<agent_name>，身份证号码：<agent_id_card>，手机号码：<agent_phone>，企业名称：<org_name>，企业法定代表人：<org_legal_person>，企业统一社会信用代码：<org_register_no>，法人证件号：<org_legal_person_id_card>。再对<url/file_name.pdf>进行数字签名。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - imagePath: string? - 印章图片的绝对路径或URL地址
  - pageIndex: number - 添加印章页码，将放置签名的页索引（从1开始）
  - signatureRect: string - 印章坐标位置，PDF坐标系，格式：[left, bottom, right, top]
  - certId: string - 证书ID
  - appearanceFlag: string? - 外观标志，可选值数组 JSON，如 ["APFlagReason","APFlagSigningTime"]
  - signer: string? - 签名者名称
  - text: string? - 签名文本内容
  - location: string? - 签名地点
  - reason: string? - 签名原因
  - contactInfo: string? - 联系信息

### pages_basic_info

获取PDF文档的基本信息。使用示例1：获取<absolute_path/file_name.pdf>的基本信息。使用示例2：获取<url/file_name.pdf>的基本信息，页面范围为：1-5。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - pageRange: string? - 页面范围 (如 1,2,5-9,all)

### pages_is_scanned

获取PDF文档的扫描状态。使用示例1：获取<absolute_path/file_name.pdf>的扫描状态。使用示例2：获取<url/file_name.pdf>的扫描状态，页面范围为：1-5。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - pageRange: string? - 页面范围

### watermark_pdf

给PDF文档添加水印。使用示例1：给<absolute_path/file_name.pdf>添加文本水印，文本为：<font_text>。使用示例2：给<url/file_name.pdf>添加图片水印，水印图片为：<absolute_path/file_name.png>。

参数：
  - path: string - PDF文档的绝对路径或URL地址
  - imagePath: string? - 水印图片的绝对路径或URL地址（imageObject 时必填）
  - pageRange: string? - 页面范围
  - type: enum('textObject','imageObject') - 水印类型
  - position: number? - 位置 0-8
  - offsetX / offsetY: number? - 偏移
  - flagOnTopOfPage / flagNoPrint / flagInvisible: number? - 标志位
  - scaleX / scaleY: number - 缩放比例
  - rotation: number? - 旋转角度
  - opacity: number? - 透明度 0-100
  - font: object? - 文本水印字体信息 (text, size, fontName, color, style, alignment, lineSpace)

## 在 VS Code 的 GitHub Copilot 中使用

打开 VS Code 配置文件 `mcp.json`，添加以下配置，并替换其中的 `your_client_id`：

```json
{
  "servers": {
    // 其他配置 ...
    "mcp-server-foxit-cloudapi": {
      "command": "uvx",
      "args": [
        "mcp-server-foxit-cloudapi"
      ],
      "env": {
        "CLIENT_ID": "your_client_id"
      }
    }
    // 其他配置 ...
  }
}
```

## 在 VS Code 的 Cline 中使用

打开 Cline MCP 配置文件 `cline_mcp_settings.json`, 添加以下配置，并替换其中的 `your_client_id`：

```json
{
  "mcpServers": {
    // 其他配置 ...
    "mcp-server-foxit-cloudapi": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 60,
      "command": "uvx",
      "args": [
        "mcp-server-foxit-cloudapi"
      ],
      "env": {
        "CLIENT_ID": "your_client_id"
      },
      "transportType": "stdio"
    }
    // 其他配置 ...
  }
}
```
