import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import typing

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class Request(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class Empty(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        def __init__(self) -> None: ...
    class AriaSnapShot(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        LOCATOR_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        locator: builtins.str
        strict: builtins.bool
        def __init__(self, *, locator: builtins.str = ..., strict: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['locator', 'locator', 'strict', 'strict']) -> None: ...
    class ClosePage(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        RUNBEFOREUNLOAD_FIELD_NUMBER: builtins.int
        runBeforeUnload: builtins.bool
        def __init__(self, *, runBeforeUnload: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['runBeforeUnload', 'runBeforeUnload']) -> None: ...
    class ClockSetTime(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        TIME_FIELD_NUMBER: builtins.int
        SETTYPE_FIELD_NUMBER: builtins.int
        time: builtins.int
        setType: builtins.str
        def __init__(self, *, time: builtins.int = ..., setType: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['setType', 'setType', 'time', 'time']) -> None: ...
    class ClockAdvance(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        TIME_FIELD_NUMBER: builtins.int
        ADVANCETYPE_FIELD_NUMBER: builtins.int
        time: builtins.int
        advanceType: builtins.str
        def __init__(self, *, time: builtins.int = ..., advanceType: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['advanceType', 'advanceType', 'time', 'time']) -> None: ...
    class CoverageStart(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        COVERAGETYPE_FIELD_NUMBER: builtins.int
        RESETONNAVIGATION_FIELD_NUMBER: builtins.int
        REPORTANONYMOUSSCRIPTS_FIELD_NUMBER: builtins.int
        CONFIGFILE_FIELD_NUMBER: builtins.int
        COVERAGEDIR_FIELD_NUMBER: builtins.int
        RAW_FIELD_NUMBER: builtins.int
        coverageType: builtins.str
        resetOnNavigation: builtins.bool
        reportAnonymousScripts: builtins.bool
        configFile: builtins.str
        coverageDir: builtins.str
        raw: builtins.bool
        def __init__(self, *, coverageType: builtins.str = ..., resetOnNavigation: builtins.bool = ..., reportAnonymousScripts: builtins.bool = ..., configFile: builtins.str = ..., coverageDir: builtins.str = ..., raw: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['configFile', 'configFile', 'coverageDir', 'coverageDir', 'coverageType', 'coverageType', 'raw', 'raw', 'reportAnonymousScripts', 'reportAnonymousScripts', 'resetOnNavigation', 'resetOnNavigation']) -> None: ...
    class CoverageMerge(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        INPUT_FOLDER_FIELD_NUMBER: builtins.int
        OUTPUT_FOLDER_FIELD_NUMBER: builtins.int
        CONFIG_FIELD_NUMBER: builtins.int
        NAME_FIELD_NUMBER: builtins.int
        REPORTS_FIELD_NUMBER: builtins.int
        input_folder: builtins.str
        output_folder: builtins.str
        config: builtins.str
        name: builtins.str
        @property
        def reports(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
        def __init__(self, *, input_folder: builtins.str = ..., output_folder: builtins.str = ..., config: builtins.str = ..., name: builtins.str = ..., reports: collections.abc.Iterable[builtins.str] | None = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['config', 'config', 'input_folder', 'input_folder', 'name', 'name', 'output_folder', 'output_folder', 'reports', 'reports']) -> None: ...
    class TraceGroup(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        NAME_FIELD_NUMBER: builtins.int
        FILE_FIELD_NUMBER: builtins.int
        LINE_FIELD_NUMBER: builtins.int
        COLUMN_FIELD_NUMBER: builtins.int
        CONTEXTID_FIELD_NUMBER: builtins.int
        name: builtins.str
        file: builtins.str
        line: builtins.int
        column: builtins.int
        contextId: builtins.str
        def __init__(self, *, name: builtins.str = ..., file: builtins.str = ..., line: builtins.int = ..., column: builtins.int = ..., contextId: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['column', 'column', 'contextId', 'contextId', 'file', 'file', 'line', 'line', 'name', 'name']) -> None: ...
    class Label(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        LABEL_FIELD_NUMBER: builtins.int
        label: builtins.str
        def __init__(self, *, label: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['label', 'label']) -> None: ...
    class GetByOptions(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        STRATEGY_FIELD_NUMBER: builtins.int
        TEXT_FIELD_NUMBER: builtins.int
        OPTIONS_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        ALL_FIELD_NUMBER: builtins.int
        FRAMESELECTOR_FIELD_NUMBER: builtins.int
        strategy: builtins.str
        text: builtins.str
        options: builtins.str
        strict: builtins.bool
        all: builtins.bool
        frameSelector: builtins.str
        def __init__(self, *, strategy: builtins.str = ..., text: builtins.str = ..., options: builtins.str = ..., strict: builtins.bool = ..., all: builtins.bool = ..., frameSelector: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['all', 'all', 'frameSelector', 'frameSelector', 'options', 'options', 'strategy', 'strategy', 'strict', 'strict', 'text', 'text']) -> None: ...
    class Pdf(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        DISPLAYHEADERFOOTER_FIELD_NUMBER: builtins.int
        FOOTERTEMPLATE_FIELD_NUMBER: builtins.int
        FORMAT_FIELD_NUMBER: builtins.int
        HEADERTEMPLATE_FIELD_NUMBER: builtins.int
        HEIGHT_FIELD_NUMBER: builtins.int
        LANDSCAPE_FIELD_NUMBER: builtins.int
        MARGIN_FIELD_NUMBER: builtins.int
        OUTLINE_FIELD_NUMBER: builtins.int
        PAGERANGES_FIELD_NUMBER: builtins.int
        PATH_FIELD_NUMBER: builtins.int
        PREFERCSSPAGESIZE_FIELD_NUMBER: builtins.int
        PRINTBACKGROUND_FIELD_NUMBER: builtins.int
        SCALE_FIELD_NUMBER: builtins.int
        TAGGED_FIELD_NUMBER: builtins.int
        WIDTH_FIELD_NUMBER: builtins.int
        displayHeaderFooter: builtins.bool
        footerTemplate: builtins.str
        format: builtins.str
        headerTemplate: builtins.str
        height: builtins.str
        landscape: builtins.bool
        margin: builtins.str
        outline: builtins.bool
        pageRanges: builtins.str
        path: builtins.str
        preferCSSPageSize: builtins.bool
        printBackground: builtins.bool
        scale: builtins.float
        tagged: builtins.bool
        width: builtins.str
        def __init__(self, *, displayHeaderFooter: builtins.bool = ..., footerTemplate: builtins.str = ..., format: builtins.str = ..., headerTemplate: builtins.str = ..., height: builtins.str = ..., landscape: builtins.bool = ..., margin: builtins.str = ..., outline: builtins.bool = ..., pageRanges: builtins.str = ..., path: builtins.str = ..., preferCSSPageSize: builtins.bool = ..., printBackground: builtins.bool = ..., scale: builtins.float = ..., tagged: builtins.bool = ..., width: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['displayHeaderFooter', 'displayHeaderFooter', 'footerTemplate', 'footerTemplate', 'format', 'format', 'headerTemplate', 'headerTemplate', 'height', 'height', 'landscape', 'landscape', 'margin', 'margin', 'outline', 'outline', 'pageRanges', 'pageRanges', 'path', 'path', 'preferCSSPageSize', 'preferCSSPageSize', 'printBackground', 'printBackground', 'scale', 'scale', 'tagged', 'tagged', 'width', 'width']) -> None: ...
    class EmulateMedia(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        COLORSCHEME_FIELD_NUMBER: builtins.int
        FORCEDCOLORS_FIELD_NUMBER: builtins.int
        MEDIA_FIELD_NUMBER: builtins.int
        REDUCEDMOTION_FIELD_NUMBER: builtins.int
        colorScheme: builtins.str
        forcedColors: builtins.str
        media: builtins.str
        reducedMotion: builtins.str
        def __init__(self, *, colorScheme: builtins.str = ..., forcedColors: builtins.str = ..., media: builtins.str = ..., reducedMotion: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['colorScheme', 'colorScheme', 'forcedColors', 'forcedColors', 'media', 'media', 'reducedMotion', 'reducedMotion']) -> None: ...
    class ScreenshotOptions(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        MASK_FIELD_NUMBER: builtins.int
        OPTIONS_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        selector: builtins.str
        mask: builtins.str
        options: builtins.str
        strict: builtins.bool
        def __init__(self, *, selector: builtins.str = ..., mask: builtins.str = ..., options: builtins.str = ..., strict: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['mask', 'mask', 'options', 'options', 'selector', 'selector', 'strict', 'strict']) -> None: ...
    class KeywordCall(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        NAME_FIELD_NUMBER: builtins.int
        ARGUMENTS_FIELD_NUMBER: builtins.int
        name: builtins.str
        arguments: builtins.str
        def __init__(self, *, name: builtins.str = ..., arguments: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['arguments', 'arguments', 'name', 'name']) -> None: ...
    class FilePath(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        PATH_FIELD_NUMBER: builtins.int
        path: builtins.str
        def __init__(self, *, path: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['path', 'path']) -> None: ...
    class FileBySelector(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        PATH_FIELD_NUMBER: builtins.int
        SELECTOR_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        NAME_FIELD_NUMBER: builtins.int
        MIMETYPE_FIELD_NUMBER: builtins.int
        BUFFER_FIELD_NUMBER: builtins.int
        selector: builtins.str
        strict: builtins.bool
        name: builtins.str
        mimeType: builtins.str
        buffer: builtins.str
        @property
        def path(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
        def __init__(self, *, path: collections.abc.Iterable[builtins.str] | None = ..., selector: builtins.str = ..., strict: builtins.bool = ..., name: builtins.str = ..., mimeType: builtins.str = ..., buffer: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['buffer', 'buffer', 'mimeType', 'mimeType', 'name', 'name', 'path', 'path', 'selector', 'selector', 'strict', 'strict']) -> None: ...
    class LocatorHandlerAddCustom(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        NOWAITAFTER_FIELD_NUMBER: builtins.int
        TIMES_FIELD_NUMBER: builtins.int
        HANDLERSPECS_FIELD_NUMBER: builtins.int
        selector: builtins.str
        noWaitAfter: builtins.bool
        times: builtins.str
        @property
        def handlerSpecs(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___Request.LocatorHandlerAddCustomAction]: ...
        def __init__(self, *, selector: builtins.str = ..., noWaitAfter: builtins.bool = ..., times: builtins.str = ..., handlerSpecs: collections.abc.Iterable[global___Request.LocatorHandlerAddCustomAction] | None = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['handlerSpecs', 'handlerSpecs', 'noWaitAfter', 'noWaitAfter', 'selector', 'selector', 'times', 'times']) -> None: ...
    class LocatorHandlerAddCustomAction(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ACTION_FIELD_NUMBER: builtins.int
        SELECTOR_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        OPTIONSASJSON_FIELD_NUMBER: builtins.int
        action: builtins.str
        selector: builtins.str
        value: builtins.str
        optionsAsJson: builtins.str
        def __init__(self, *, action: builtins.str = ..., selector: builtins.str = ..., value: builtins.str = ..., optionsAsJson: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['action', 'action', 'optionsAsJson', 'optionsAsJson', 'selector', 'selector', 'value', 'value']) -> None: ...
    class LocatorHandlerRemove(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        selector: builtins.str
        def __init__(self, *, selector: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['selector', 'selector']) -> None: ...
    class Json(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        BODY_FIELD_NUMBER: builtins.int
        body: builtins.str
        def __init__(self, *, body: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['body', 'body']) -> None: ...
    class MouseButtonOptions(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ACTION_FIELD_NUMBER: builtins.int
        JSON_FIELD_NUMBER: builtins.int
        action: builtins.str
        json: builtins.str
        def __init__(self, *, action: builtins.str = ..., json: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['action', 'action', 'json', 'json']) -> None: ...
    class MouseWheel(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        DELTAX_FIELD_NUMBER: builtins.int
        DELTAY_FIELD_NUMBER: builtins.int
        deltaX: builtins.int
        deltaY: builtins.int
        def __init__(self, *, deltaX: builtins.int = ..., deltaY: builtins.int = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['deltaX', 'deltaX', 'deltaY', 'deltaY']) -> None: ...
    class KeyboardKeypress(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ACTION_FIELD_NUMBER: builtins.int
        KEY_FIELD_NUMBER: builtins.int
        action: builtins.str
        key: builtins.str
        def __init__(self, *, action: builtins.str = ..., key: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['action', 'action', 'key', 'key']) -> None: ...
    class KeyboardInputOptions(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ACTION_FIELD_NUMBER: builtins.int
        INPUT_FIELD_NUMBER: builtins.int
        DELAY_FIELD_NUMBER: builtins.int
        action: builtins.str
        input: builtins.str
        delay: builtins.int
        def __init__(self, *, action: builtins.str = ..., input: builtins.str = ..., delay: builtins.int = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['action', 'action', 'delay', 'delay', 'input', 'input']) -> None: ...
    class Browser(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        BROWSER_FIELD_NUMBER: builtins.int
        RAWOPTIONS_FIELD_NUMBER: builtins.int
        browser: builtins.str
        rawOptions: builtins.str
        def __init__(self, *, browser: builtins.str = ..., rawOptions: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['browser', 'browser', 'rawOptions', 'rawOptions']) -> None: ...
    class Context(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        RAWOPTIONS_FIELD_NUMBER: builtins.int
        DEFAULTTIMEOUT_FIELD_NUMBER: builtins.int
        TRACEFILE_FIELD_NUMBER: builtins.int
        rawOptions: builtins.str
        defaultTimeout: builtins.int
        traceFile: builtins.str
        def __init__(self, *, rawOptions: builtins.str = ..., defaultTimeout: builtins.int = ..., traceFile: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['defaultTimeout', 'defaultTimeout', 'rawOptions', 'rawOptions', 'traceFile', 'traceFile']) -> None: ...
    class PersistentContext(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        BROWSER_FIELD_NUMBER: builtins.int
        RAWOPTIONS_FIELD_NUMBER: builtins.int
        DEFAULTTIMEOUT_FIELD_NUMBER: builtins.int
        TRACEFILE_FIELD_NUMBER: builtins.int
        browser: builtins.str
        rawOptions: builtins.str
        defaultTimeout: builtins.int
        traceFile: builtins.str
        def __init__(self, *, browser: builtins.str = ..., rawOptions: builtins.str = ..., defaultTimeout: builtins.int = ..., traceFile: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['browser', 'browser', 'defaultTimeout', 'defaultTimeout', 'rawOptions', 'rawOptions', 'traceFile', 'traceFile']) -> None: ...
    class Permissions(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        PERMISSIONS_FIELD_NUMBER: builtins.int
        ORIGIN_FIELD_NUMBER: builtins.int
        origin: builtins.str
        @property
        def permissions(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
        def __init__(self, *, permissions: collections.abc.Iterable[builtins.str] | None = ..., origin: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['origin', 'origin', 'permissions', 'permissions']) -> None: ...
    class Url(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        URL_FIELD_NUMBER: builtins.int
        DEFAULTTIMEOUT_FIELD_NUMBER: builtins.int
        url: builtins.str
        defaultTimeout: builtins.int
        def __init__(self, *, url: builtins.str = ..., defaultTimeout: builtins.int = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['defaultTimeout', 'defaultTimeout', 'url', 'url']) -> None: ...
    class DownloadOptions(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        URL_FIELD_NUMBER: builtins.int
        PATH_FIELD_NUMBER: builtins.int
        WAITFORFINISH_FIELD_NUMBER: builtins.int
        DOWNLOADTIMEOUT_FIELD_NUMBER: builtins.int
        url: builtins.str
        path: builtins.str
        waitForFinish: builtins.bool
        downloadTimeout: builtins.int
        def __init__(self, *, url: builtins.str = ..., path: builtins.str = ..., waitForFinish: builtins.bool = ..., downloadTimeout: builtins.int = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['downloadTimeout', 'downloadTimeout', 'path', 'path', 'url', 'url', 'waitForFinish', 'waitForFinish']) -> None: ...
    class DownloadID(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ID_FIELD_NUMBER: builtins.int
        id: builtins.str
        def __init__(self, *, id: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['id', 'id']) -> None: ...
    class UrlOptions(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        URL_FIELD_NUMBER: builtins.int
        WAITUNTIL_FIELD_NUMBER: builtins.int
        waitUntil: builtins.str
        @property
        def url(self) -> global___Request.Url: ...
        def __init__(self, *, url: global___Request.Url | None = ..., waitUntil: builtins.str = ...) -> None: ...
        def HasField(self, field_name: typing.Literal['url', 'url']) -> builtins.bool: ...
        def ClearField(self, field_name: typing.Literal['url', 'url', 'waitUntil', 'waitUntil']) -> None: ...
    class PageLoadState(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        STATE_FIELD_NUMBER: builtins.int
        TIMEOUT_FIELD_NUMBER: builtins.int
        state: builtins.str
        timeout: builtins.int
        def __init__(self, *, state: builtins.str = ..., timeout: builtins.int = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['state', 'state', 'timeout', 'timeout']) -> None: ...
    class ConnectBrowser(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        BROWSER_FIELD_NUMBER: builtins.int
        URL_FIELD_NUMBER: builtins.int
        CONNECTCDP_FIELD_NUMBER: builtins.int
        TIMEOUT_FIELD_NUMBER: builtins.int
        browser: builtins.str
        url: builtins.str
        connectCDP: builtins.bool
        timeout: builtins.int
        def __init__(self, *, browser: builtins.str = ..., url: builtins.str = ..., connectCDP: builtins.bool = ..., timeout: builtins.int = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['browser', 'browser', 'connectCDP', 'connectCDP', 'timeout', 'timeout', 'url', 'url']) -> None: ...
    class TextInput(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        INPUT_FIELD_NUMBER: builtins.int
        SELECTOR_FIELD_NUMBER: builtins.int
        TYPE_FIELD_NUMBER: builtins.int
        input: builtins.str
        selector: builtins.str
        type: builtins.bool
        def __init__(self, *, input: builtins.str = ..., selector: builtins.str = ..., type: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['input', 'input', 'selector', 'selector', 'type', 'type']) -> None: ...
    class ElementProperty(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        PROPERTY_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        selector: builtins.str
        property: builtins.str
        strict: builtins.bool
        def __init__(self, *, selector: builtins.str = ..., property: builtins.str = ..., strict: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['property', 'property', 'selector', 'selector', 'strict', 'strict']) -> None: ...
    class TypeText(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        TEXT_FIELD_NUMBER: builtins.int
        DELAY_FIELD_NUMBER: builtins.int
        CLEAR_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        selector: builtins.str
        text: builtins.str
        delay: builtins.int
        clear: builtins.bool
        strict: builtins.bool
        def __init__(self, *, selector: builtins.str = ..., text: builtins.str = ..., delay: builtins.int = ..., clear: builtins.bool = ..., strict: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['clear', 'clear', 'delay', 'delay', 'selector', 'selector', 'strict', 'strict', 'text', 'text']) -> None: ...
    class FillText(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        TEXT_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        FORCE_FIELD_NUMBER: builtins.int
        selector: builtins.str
        text: builtins.str
        strict: builtins.bool
        force: builtins.bool
        def __init__(self, *, selector: builtins.str = ..., text: builtins.str = ..., strict: builtins.bool = ..., force: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['force', 'force', 'selector', 'selector', 'strict', 'strict', 'text', 'text']) -> None: ...
    class ClearText(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        selector: builtins.str
        strict: builtins.bool
        def __init__(self, *, selector: builtins.str = ..., strict: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['selector', 'selector', 'strict', 'strict']) -> None: ...
    class PressKeys(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        KEY_FIELD_NUMBER: builtins.int
        PRESSDELAY_FIELD_NUMBER: builtins.int
        KEYDELAY_FIELD_NUMBER: builtins.int
        selector: builtins.str
        strict: builtins.bool
        pressDelay: builtins.int
        keyDelay: builtins.int
        @property
        def key(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
        def __init__(self, *, selector: builtins.str = ..., strict: builtins.bool = ..., key: collections.abc.Iterable[builtins.str] | None = ..., pressDelay: builtins.int = ..., keyDelay: builtins.int = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['key', 'key', 'keyDelay', 'keyDelay', 'pressDelay', 'pressDelay', 'selector', 'selector', 'strict', 'strict']) -> None: ...
    class ElementSelector(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        FORCE_FIELD_NUMBER: builtins.int
        selector: builtins.str
        strict: builtins.bool
        force: builtins.bool
        def __init__(self, *, selector: builtins.str = ..., strict: builtins.bool = ..., force: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['force', 'force', 'selector', 'selector', 'strict', 'strict']) -> None: ...
    class Timeout(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        TIMEOUT_FIELD_NUMBER: builtins.int
        timeout: builtins.float
        def __init__(self, *, timeout: builtins.float = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['timeout', 'timeout']) -> None: ...
    class Index(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        INDEX_FIELD_NUMBER: builtins.int
        index: builtins.str
        def __init__(self, *, index: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['index', 'index']) -> None: ...
    class IdWithTimeout(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ID_FIELD_NUMBER: builtins.int
        TIMEOUT_FIELD_NUMBER: builtins.int
        id: builtins.str
        timeout: builtins.float
        def __init__(self, *, id: builtins.str = ..., timeout: builtins.float = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['id', 'id', 'timeout', 'timeout']) -> None: ...
    class StyleTag(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        CONTENT_FIELD_NUMBER: builtins.int
        content: builtins.str
        def __init__(self, *, content: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['content', 'content']) -> None: ...
    class ElementSelectorWithOptions(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        OPTIONS_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        selector: builtins.str
        options: builtins.str
        strict: builtins.bool
        def __init__(self, *, selector: builtins.str = ..., options: builtins.str = ..., strict: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['options', 'options', 'selector', 'selector', 'strict', 'strict']) -> None: ...
    class ElementSelectorWithDuration(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        DURATION_FIELD_NUMBER: builtins.int
        WIDTH_FIELD_NUMBER: builtins.int
        STYLE_FIELD_NUMBER: builtins.int
        COLOR_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        MODE_FIELD_NUMBER: builtins.int
        selector: builtins.str
        duration: builtins.int
        width: builtins.str
        style: builtins.str
        color: builtins.str
        strict: builtins.bool
        mode: builtins.str
        def __init__(self, *, selector: builtins.str = ..., duration: builtins.int = ..., width: builtins.str = ..., style: builtins.str = ..., color: builtins.str = ..., strict: builtins.bool = ..., mode: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['color', 'color', 'duration', 'duration', 'mode', 'mode', 'selector', 'selector', 'strict', 'strict', 'style', 'style', 'width', 'width']) -> None: ...
    class SelectElementSelector(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        MATCHERJSON_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        selector: builtins.str
        matcherJson: builtins.str
        strict: builtins.bool
        def __init__(self, *, selector: builtins.str = ..., matcherJson: builtins.str = ..., strict: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['matcherJson', 'matcherJson', 'selector', 'selector', 'strict', 'strict']) -> None: ...
    class WaitForFunctionOptions(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SCRIPT_FIELD_NUMBER: builtins.int
        SELECTOR_FIELD_NUMBER: builtins.int
        OPTIONS_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        script: builtins.str
        selector: builtins.str
        options: builtins.str
        strict: builtins.bool
        def __init__(self, *, script: builtins.str = ..., selector: builtins.str = ..., options: builtins.str = ..., strict: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['options', 'options', 'script', 'script', 'selector', 'selector', 'strict', 'strict']) -> None: ...
    class PlaywrightObject(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        INFO_FIELD_NUMBER: builtins.int
        info: builtins.str
        def __init__(self, *, info: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['info', 'info']) -> None: ...
    class Viewport(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        WIDTH_FIELD_NUMBER: builtins.int
        HEIGHT_FIELD_NUMBER: builtins.int
        width: builtins.int
        height: builtins.int
        def __init__(self, *, width: builtins.int = ..., height: builtins.int = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['height', 'height', 'width', 'width']) -> None: ...
    class HttpRequest(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        URL_FIELD_NUMBER: builtins.int
        METHOD_FIELD_NUMBER: builtins.int
        BODY_FIELD_NUMBER: builtins.int
        HEADERS_FIELD_NUMBER: builtins.int
        url: builtins.str
        method: builtins.str
        body: builtins.str
        headers: builtins.str
        def __init__(self, *, url: builtins.str = ..., method: builtins.str = ..., body: builtins.str = ..., headers: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['body', 'body', 'headers', 'headers', 'method', 'method', 'url', 'url']) -> None: ...
    class HttpCapture(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        URLORPREDICATE_FIELD_NUMBER: builtins.int
        TIMEOUT_FIELD_NUMBER: builtins.int
        urlOrPredicate: builtins.str
        timeout: builtins.float
        def __init__(self, *, urlOrPredicate: builtins.str = ..., timeout: builtins.float = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['timeout', 'timeout', 'urlOrPredicate', 'urlOrPredicate']) -> None: ...
    class Device(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        NAME_FIELD_NUMBER: builtins.int
        name: builtins.str
        def __init__(self, *, name: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['name', 'name']) -> None: ...
    class AlertAction(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ALERTACTION_FIELD_NUMBER: builtins.int
        PROMPTINPUT_FIELD_NUMBER: builtins.int
        TIMEOUT_FIELD_NUMBER: builtins.int
        alertAction: builtins.str
        promptInput: builtins.str
        timeout: builtins.float
        def __init__(self, *, alertAction: builtins.str = ..., promptInput: builtins.str = ..., timeout: builtins.float = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['alertAction', 'alertAction', 'promptInput', 'promptInput', 'timeout', 'timeout']) -> None: ...
    class AlertActions(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ITEMS_FIELD_NUMBER: builtins.int
        @property
        def items(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___Request.AlertAction]: ...
        def __init__(self, *, items: collections.abc.Iterable[global___Request.AlertAction] | None = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['items', 'items']) -> None: ...
    class Bool(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        VALUE_FIELD_NUMBER: builtins.int
        value: builtins.bool
        def __init__(self, *, value: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['value', 'value']) -> None: ...
    class EvaluateAll(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        SCRIPT_FIELD_NUMBER: builtins.int
        ARG_FIELD_NUMBER: builtins.int
        ALLELEMENTS_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        selector: builtins.str
        script: builtins.str
        arg: builtins.str
        allElements: builtins.bool
        strict: builtins.bool
        def __init__(self, *, selector: builtins.str = ..., script: builtins.str = ..., arg: builtins.str = ..., allElements: builtins.bool = ..., strict: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['allElements', 'allElements', 'arg', 'arg', 'script', 'script', 'selector', 'selector', 'strict', 'strict']) -> None: ...
    class ElementStyle(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        SELECTOR_FIELD_NUMBER: builtins.int
        PSEUDO_FIELD_NUMBER: builtins.int
        STYLEKEY_FIELD_NUMBER: builtins.int
        STRICT_FIELD_NUMBER: builtins.int
        selector: builtins.str
        pseudo: builtins.str
        styleKey: builtins.str
        strict: builtins.bool
        def __init__(self, *, selector: builtins.str = ..., pseudo: builtins.str = ..., styleKey: builtins.str = ..., strict: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['pseudo', 'pseudo', 'selector', 'selector', 'strict', 'strict', 'styleKey', 'styleKey']) -> None: ...
    def __init__(self) -> None: ...
global___Request = Request

class Types(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class SelectEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        VALUE_FIELD_NUMBER: builtins.int
        LABEL_FIELD_NUMBER: builtins.int
        INDEX_FIELD_NUMBER: builtins.int
        SELECTED_FIELD_NUMBER: builtins.int
        value: builtins.str
        label: builtins.str
        index: builtins.int
        selected: builtins.bool
        def __init__(self, *, value: builtins.str = ..., label: builtins.str = ..., index: builtins.int = ..., selected: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['index', 'index', 'label', 'label', 'selected', 'selected', 'value', 'value']) -> None: ...
    def __init__(self) -> None: ...
global___Types = Types

class Response(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class Empty(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        LOG_FIELD_NUMBER: builtins.int
        log: builtins.str
        def __init__(self, *, log: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['log', 'log']) -> None: ...
    class String(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        LOG_FIELD_NUMBER: builtins.int
        BODY_FIELD_NUMBER: builtins.int
        log: builtins.str
        body: builtins.str
        def __init__(self, *, log: builtins.str = ..., body: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['body', 'body', 'log', 'log']) -> None: ...
    class ListString(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ITEMS_FIELD_NUMBER: builtins.int
        @property
        def items(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
        def __init__(self, *, items: collections.abc.Iterable[builtins.str] | None = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['items', 'items']) -> None: ...
    class Keywords(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        LOG_FIELD_NUMBER: builtins.int
        KEYWORDS_FIELD_NUMBER: builtins.int
        KEYWORDDOCUMENTATIONS_FIELD_NUMBER: builtins.int
        KEYWORDARGUMENTS_FIELD_NUMBER: builtins.int
        log: builtins.str
        @property
        def keywords(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
        @property
        def keywordDocumentations(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
        @property
        def keywordArguments(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
        def __init__(self, *, log: builtins.str = ..., keywords: collections.abc.Iterable[builtins.str] | None = ..., keywordDocumentations: collections.abc.Iterable[builtins.str] | None = ..., keywordArguments: collections.abc.Iterable[builtins.str] | None = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['keywordArguments', 'keywordArguments', 'keywordDocumentations', 'keywordDocumentations', 'keywords', 'keywords', 'log', 'log']) -> None: ...
    class Bool(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        LOG_FIELD_NUMBER: builtins.int
        BODY_FIELD_NUMBER: builtins.int
        log: builtins.str
        body: builtins.bool
        def __init__(self, *, log: builtins.str = ..., body: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['body', 'body', 'log', 'log']) -> None: ...
    class Int(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        LOG_FIELD_NUMBER: builtins.int
        BODY_FIELD_NUMBER: builtins.int
        log: builtins.str
        body: builtins.int
        def __init__(self, *, log: builtins.str = ..., body: builtins.int = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['body', 'body', 'log', 'log']) -> None: ...
    class Select(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ENTRY_FIELD_NUMBER: builtins.int
        @property
        def entry(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___Types.SelectEntry]: ...
        def __init__(self, *, entry: collections.abc.Iterable[global___Types.SelectEntry] | None = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['entry', 'entry']) -> None: ...
    class Json(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        LOG_FIELD_NUMBER: builtins.int
        JSON_FIELD_NUMBER: builtins.int
        BODYPART_FIELD_NUMBER: builtins.int
        log: builtins.str
        json: builtins.str
        bodyPart: builtins.str
        def __init__(self, *, log: builtins.str = ..., json: builtins.str = ..., bodyPart: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['bodyPart', 'bodyPart', 'json', 'json', 'log', 'log']) -> None: ...
    class JavascriptExecutionResult(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        LOG_FIELD_NUMBER: builtins.int
        RESULT_FIELD_NUMBER: builtins.int
        log: builtins.str
        result: builtins.str
        def __init__(self, *, log: builtins.str = ..., result: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['log', 'log', 'result', 'result']) -> None: ...
    class NewContextResponse(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ID_FIELD_NUMBER: builtins.int
        LOG_FIELD_NUMBER: builtins.int
        CONTEXTOPTIONS_FIELD_NUMBER: builtins.int
        NEWBROWSER_FIELD_NUMBER: builtins.int
        id: builtins.str
        log: builtins.str
        contextOptions: builtins.str
        newBrowser: builtins.bool
        def __init__(self, *, id: builtins.str = ..., log: builtins.str = ..., contextOptions: builtins.str = ..., newBrowser: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['contextOptions', 'contextOptions', 'id', 'id', 'log', 'log', 'newBrowser', 'newBrowser']) -> None: ...
    class NewPersistentContextResponse(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ID_FIELD_NUMBER: builtins.int
        LOG_FIELD_NUMBER: builtins.int
        CONTEXTOPTIONS_FIELD_NUMBER: builtins.int
        NEWBROWSER_FIELD_NUMBER: builtins.int
        VIDEO_FIELD_NUMBER: builtins.int
        PAGEID_FIELD_NUMBER: builtins.int
        BROWSERID_FIELD_NUMBER: builtins.int
        id: builtins.str
        log: builtins.str
        contextOptions: builtins.str
        newBrowser: builtins.bool
        video: builtins.str
        pageId: builtins.str
        browserId: builtins.str
        def __init__(self, *, id: builtins.str = ..., log: builtins.str = ..., contextOptions: builtins.str = ..., newBrowser: builtins.bool = ..., video: builtins.str = ..., pageId: builtins.str = ..., browserId: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['browserId', 'browserId', 'contextOptions', 'contextOptions', 'id', 'id', 'log', 'log', 'newBrowser', 'newBrowser', 'pageId', 'pageId', 'video', 'video']) -> None: ...
    class NewPageResponse(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        LOG_FIELD_NUMBER: builtins.int
        BODY_FIELD_NUMBER: builtins.int
        VIDEO_FIELD_NUMBER: builtins.int
        NEWBROWSER_FIELD_NUMBER: builtins.int
        NEWCONTEXT_FIELD_NUMBER: builtins.int
        log: builtins.str
        body: builtins.str
        video: builtins.str
        newBrowser: builtins.bool
        newContext: builtins.bool
        def __init__(self, *, log: builtins.str = ..., body: builtins.str = ..., video: builtins.str = ..., newBrowser: builtins.bool = ..., newContext: builtins.bool = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['body', 'body', 'log', 'log', 'newBrowser', 'newBrowser', 'newContext', 'newContext', 'video', 'video']) -> None: ...
    class PageReportResponse(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        LOG_FIELD_NUMBER: builtins.int
        ERRORS_FIELD_NUMBER: builtins.int
        CONSOLE_FIELD_NUMBER: builtins.int
        PAGEID_FIELD_NUMBER: builtins.int
        log: builtins.str
        errors: builtins.str
        console: builtins.str
        pageId: builtins.str
        def __init__(self, *, log: builtins.str = ..., errors: builtins.str = ..., console: builtins.str = ..., pageId: builtins.str = ...) -> None: ...
        def ClearField(self, field_name: typing.Literal['console', 'console', 'errors', 'errors', 'log', 'log', 'pageId', 'pageId']) -> None: ...
    def __init__(self) -> None: ...
global___Response = Response
